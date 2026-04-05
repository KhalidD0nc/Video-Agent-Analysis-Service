"""
Modal Deployment — CoachAI Video Analysis Agent
================================================

Production-ready inference service for T-DEED soccer action spotting
combined with Gemini tactical analysis.

Architecture:
    POST /submit   → spawns async GPU job, returns job_id
    GET  /status   → polls job status by job_id, returns result when done
    POST /analyze  → synchronous (for short videos / testing only)

Usage:
    Development:  modal serve modal_app.py
    Production:   modal deploy modal_app.py
"""

import modal
import os
import json
import time
import uuid
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. APP & INFRASTRUCTURE DEFINITIONS
# ---------------------------------------------------------------------------

app = modal.App("coachAI-video-analysis")

# Persistent storage for model checkpoints (uploaded via upload_weights.py)
volume = modal.Volume.from_name("coachAI-weights", create_if_missing=True)
WEIGHTS_DIR = Path("/weights")

# Container image with all dependencies baked in
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1", "libglib2.0-0", "ffmpeg", "curl", "unzip")
    .run_commands(
        "curl -fsSL https://deno.land/install.sh | sh",
        "mv /root/.deno/bin/deno /usr/local/bin/deno"
    )
    .pip_install(
        # Core AI
        "torch==2.5.1",
        "torchvision==0.20.1",
        "timm==1.0.24",
        "SoccerNet==0.1.62",
        "opencv-python-headless==4.13.0.92",
        "huggingface-hub==1.4.1",
        # Data Science
        "numpy==2.3.5",
        "pandas==3.0.1",
        "scikit-learn==1.8.0",
        "scipy==1.17.0",
        "pillow==11.3.0",
        # Utilities
        "tqdm==4.67.3",
        "tabulate==0.9.0",
        "PyYAML==6.0.3",
        # Pipeline (Gemini + YouTube)
        "google-genai==1.64.0",
        "yt-dlp==2026.2.21",
        "python-dotenv==1.2.1",
        # Web endpoints (required explicitly in Modal v1)
        "fastapi[standard]",
    )
    # All build steps MUST come before add_local_dir() in Modal v1
    .env({
        "WANDB_MODE": "offline",
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
    })
    # Bake source code INTO the image last (Modal v1 rule: add_local_* must be last)
    .add_local_dir(
        os.path.join(os.path.dirname(__file__), "model"),
        remote_path="/root/app/model",
    )
    .add_local_dir(
        os.path.join(os.path.dirname(__file__), "dataset"),
        remote_path="/root/app/dataset",
    )
    .add_local_dir(
        os.path.join(os.path.dirname(__file__), "util"),
        remote_path="/root/app/util",
    )
)

# Models to run (same as run_pipeline.py)
MODELS_TO_RUN = ["SoccerNet_small", "SoccerNetBall_challenge1"]
FPS = 25


# ---------------------------------------------------------------------------
# 2. THE GPU INFERENCE SERVICE (Class-based for persistent model loading)
# ---------------------------------------------------------------------------

@app.cls(
    image=image,
    gpu=["T4", "L4", "A10"],  # Fallback chain: T4 → L4 → A10
    volumes={WEIGHTS_DIR: volume},
    secrets=[modal.Secret.from_name("gemini-api-key")],
    scaledown_window=300,     # Keep container warm for 5 min after last request
    min_containers=0,         # Scale to zero when idle (set to 1 for demo day)
    max_containers=3,         # Cap concurrent containers
    timeout=900,              # 15-minute max per invocation
)
class CoachAIService:
    """
    Persistent GPU container that loads both T-DEED models once on boot
    and serves inference requests.
    """

    @modal.enter()
    def load_models(self):
        """Called once when the container boots. Loads both models into GPU memory."""
        import sys
        import torch

        # Add source code to Python path
        sys.path.insert(0, "/root/app")

        from util.io import load_json
        from model.model import TDEEDModel
        from util.dataset import load_classes

        # Detect device
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        print(f"⚙️ Container booted on [{self.device.type.upper()}]")

        # Load both models
        self.models = {}
        self.classes = {}
        self.configs = {}

        for model_name in MODELS_TO_RUN:
            print(f"📦 Loading model: {model_name}")

            # Load config from Volume
            config_path = model_name.split("_")[0] + "/" + model_name + ".json"
            config = load_json(str(WEIGHTS_DIR / "config" / config_path))

            # Build args namespace
            args = self._build_args(model_name, config)

            # Load class definitions from Volume (class_data, not data)
            dataset_name = config["dataset"]
            classes = load_classes(str(WEIGHTS_DIR / "class_data" / dataset_name / "class.txt"))

            # Instantiate model
            model = TDEEDModel(device=self.device, args=args)

            # Handle pretrain double-head
            import numpy as np
            if args.pretrain is not None:
                pretrain_classes = load_classes(
                    str(WEIGHTS_DIR / "class_data" / args.pretrain["dataset"] / "class.txt")
                )
                n_classes = [len(classes) + 1, len(pretrain_classes) + 1]
                model._model.update_pred_head(n_classes)
                model._num_classes = np.array(n_classes).sum()

            # Load checkpoint from Volume
            checkpoint_path = str(
                WEIGHTS_DIR / "checkpoints" / model_name.split("_")[0] / model_name / "checkpoint_best.pt"
            )
            model.load(torch.load(checkpoint_path, map_location=self.device))

            self.models[model_name] = model
            self.classes[model_name] = classes
            self.configs[model_name] = config

            print(f"✅ Model {model_name} loaded successfully")

        print(f"🚀 All {len(self.models)} models loaded and ready for inference")

    def _build_args(self, model_name, config):
        """Build an args namespace from config dict (mirrors update_args in inference.py)."""
        import argparse

        args = argparse.Namespace()
        args.model = model_name
        args.frame_dir = config["frame_dir"]
        args.save_dir = config.get("save_dir", "/tmp")
        args.store_dir = config.get("store_dir", "/tmp")
        args.store_mode = config["store_mode"]
        args.batch_size = config["batch_size"]
        args.clip_len = config["clip_len"]
        args.crop_dim = config["crop_dim"]
        if args.crop_dim <= 0:
            args.crop_dim = None
        args.dataset = config["dataset"]
        args.radi_displacement = config["radi_displacement"]
        args.epoch_num_frames = config["epoch_num_frames"]
        args.feature_arch = config["feature_arch"]
        args.learning_rate = config["learning_rate"]
        args.mixup = config["mixup"]
        args.modality = config["modality"]
        args.num_classes = config["num_classes"]
        args.num_epochs = config["num_epochs"]
        args.warm_up_epochs = config["warm_up_epochs"]
        args.start_val_epoch = config["start_val_epoch"]
        args.temporal_arch = config["temporal_arch"]
        args.n_layers = config["n_layers"]
        args.sgp_ks = config["sgp_ks"]
        args.sgp_r = config["sgp_r"]
        args.only_test = config["only_test"]
        args.criterion = config["criterion"]
        args.num_workers = config["num_workers"]
        args.pretrain = config.get("pretrain", None)
        args.device = self.device
        args.acc_grad_iter = 1
        args.seed = 1

        return args

    # -------------------------------------------------------------------
    # CORE PIPELINE METHOD (called by both sync and async endpoints)
    # -------------------------------------------------------------------

    @modal.method()
    def run_pipeline(
        self,
        video_url: str = "",
        inference_threshold: float = 0.3,
        skip_gemini: bool = False,
        video_path: str = "",  # skip download — use a file already on the volume
    ) -> dict:
        """
        Execute the full 4-stage pipeline on a video.
        Returns a dict with all results.
        """
        import sys
        sys.path.insert(0, "/root/app")

        pipeline_start = time.time()
        results = {
            "status": "success",
            "stages": {},
        }

        # === STAGE 0: Download video (skipped if video_path provided) ===
        stage_start = time.time()
        if video_path:
            volume.reload()  # sync volume so files uploaded after container boot are visible
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"video_path not found: {video_path}")
            print(f"📂 Using existing file: {video_path}")
        else:
            if not video_url:
                raise ValueError("Either video_url or video_path must be provided")
            video_path = self._download_video(video_url)
        results["stages"]["download"] = {
            "duration_seconds": round(time.time() - stage_start, 1),
        }
        print(f"📥 Video ready: {video_path}")

        # === STAGE 1: Run both T-DEED models ===
        stage_start = time.time()
        all_events = {}
        for model_name in MODELS_TO_RUN:
            events = self._run_inference(model_name, video_path, inference_threshold)
            all_events[model_name] = events
            print(f"🔍 {model_name}: detected {len(events)} events")

        results["stages"]["inference"] = {
            "duration_seconds": round(time.time() - stage_start, 1),
            "events_per_model": {k: len(v) for k, v in all_events.items()},
        }

        # === STAGE 2: Data cleaning & merging ===
        stage_start = time.time()
        timeline_csv, clean_events = self._merge_and_clean(all_events)
        results["stages"]["cleaning"] = {
            "duration_seconds": round(time.time() - stage_start, 1),
            "events_after_cleaning": len(clean_events),
        }
        results["timeline_csv"] = timeline_csv
        print(f"🧹 Cleaned timeline: {len(clean_events)} unique events")

        # === STAGES 3 & 4: Gemini Analysis ===
        if not skip_gemini:
            stage_start = time.time()
            tactical_json, comprehensive_md = self._run_gemini_analysis(
                video_path, timeline_csv
            )
            results["stages"]["gemini_analysis"] = {
                "duration_seconds": round(time.time() - stage_start, 1),
            }
            results["tactical_report_json"] = tactical_json
            results["comprehensive_analysis_md"] = comprehensive_md
            print("📝 Gemini analysis complete")

        results["pipeline_duration_seconds"] = round(time.time() - pipeline_start, 1)

        # Cleanup
        if os.path.exists(video_path):
            os.remove(video_path)

        return results

    # -------------------------------------------------------------------
    # STAGE 1: T-DEED INFERENCE
    # -------------------------------------------------------------------

    def _run_inference(self, model_name: str, video_path: str, threshold: float) -> list:
        """Run a single T-DEED model on a video file."""
        import torch
        import numpy as np
        from torch.utils.data import DataLoader
        from dataset.frame import ActionSpotInferenceDataset
        from util.eval import (
            process_frame_predictions_inference,
            soft_non_maximum_supression,
        )

        config = self.configs[model_name]
        model = self.models[model_name]
        classes = self.classes[model_name]

        # Determine stride based on dataset
        STRIDE_MAP = {"soccernet": 12, "soccernetball": 2}
        stride = STRIDE_MAP.get(config["dataset"], 1)

        # Windows for NMS
        WINDOWS_MAP = {
            "soccernet": [3, 6],
            "soccernetball": [6, 12],
        }
        windows = WINDOWS_MAP.get(config["dataset"], [1, 3])

        # Build dataset
        clip_len = config["clip_len"]
        inference_dataset = ActionSpotInferenceDataset(
            video_path,
            clip_len=clip_len,
            overlap_len=clip_len // 4 * 3
            if config["dataset"] != "soccernet"
            else clip_len // 2,
            stride=stride,
            dataset=config["dataset"],
            size=(796, 448),
        )

        inference_loader = DataLoader(
            inference_dataset,
            batch_size=1,
            shuffle=False,
            num_workers=0,
            pin_memory=True if self.device.type == "cuda" else False,
            drop_last=False,
        )

        video_len = inference_dataset._video_len

        # Run inference
        from tqdm import tqdm

        predictions = np.zeros(
            (video_len // stride, len(classes) + 1), np.float32
        )
        support = np.zeros((video_len // stride), np.int32)

        for frames, starts in tqdm(
            inference_loader, desc=f"Inference [{model_name}]"
        ):
            _, batch_pred_scores = model.predict(frames)

            for i in range(frames.shape[0]):
                pred_scores = batch_pred_scores[i]
                start = starts[i].item()
                if start < 0:
                    pred_scores = pred_scores[-start:, :]
                    start = 0
                end = start + pred_scores.shape[0]
                if end >= predictions.shape[0]:
                    end = predictions.shape[0]
                    pred_scores = pred_scores[: end - start, :]

                predictions[start:end, :] += pred_scores
                support[start:end] += (pred_scores.sum(axis=1) != 0) * 1

        # Post-process
        pred_events, pred_events_high_recall, _ = process_frame_predictions_inference(
            config["dataset"], classes, predictions, support,
            high_recall_score_threshold=threshold,
        )

        pred_events_nms = soft_non_maximum_supression(
            [{"events": pred_events_high_recall}],
            window=windows[1],
            threshold=threshold,
        )

        # Convert to serializable dicts
        events = []
        for event in pred_events_nms[0]["events"]:
            events.append({
                "frame": int(event["frame"]) * stride,
                "label": event["label"],
                "confidence": round(float(event["score"]), 4),
            })

        return events

    # -------------------------------------------------------------------
    # STAGE 2: DATA CLEANING & MERGING
    # -------------------------------------------------------------------

    def _merge_and_clean(self, all_events: dict) -> tuple:
        """Merge events from both models and apply deduplication."""
        import pandas as pd

        def frame_to_time(frame):
            total_seconds = int(frame) / FPS
            return f"{int(total_seconds // 60):02d}:{int(total_seconds % 60):02d}"

        # Build DataFrames
        frames = []
        for model_name, events in all_events.items():
            event_type = (
                "Match Event" if "SoccerNet_small" in model_name else "Ball Action"
            )
            for e in events:
                frames.append({
                    "frame": e["frame"],
                    "timestamp": frame_to_time(e["frame"]),
                    "label": e["label"],
                    "confidence": e["confidence"],
                    "Event_Type": event_type,
                })

        if not frames:
            return "", []

        df = pd.DataFrame(frames)
        df = df.sort_values(by=["label", "frame"])

        # Deduplication within 3-second windows
        FRAME_WINDOW = FPS * 3
        df["frame_diff"] = df.groupby("label")["frame"].diff()
        df["event_block"] = (
            df["frame_diff"].fillna(FRAME_WINDOW + 1) > FRAME_WINDOW
        ).cumsum()
        best_indices = df.groupby(["label", "event_block"])["confidence"].idxmax()

        df_clean = df.loc[best_indices].copy()
        df_clean = df_clean.sort_values(by="frame")
        df_clean = df_clean[
            ["timestamp", "frame", "label", "confidence", "Event_Type"]
        ]
        df_clean["confidence"] = df_clean["confidence"].apply(lambda x: round(x, 2))

        csv_string = df_clean.to_csv(index=False)

        clean_events = df_clean.to_dict(orient="records")
        return csv_string, clean_events

    # -------------------------------------------------------------------
    # STAGES 3 & 4: GEMINI TACTICAL ANALYSIS
    # -------------------------------------------------------------------

    def _run_gemini_analysis(
        self, video_path: str, csv_data: str
    ) -> tuple:
        """Run Gemini analysis (JSON structured + comprehensive text report)."""
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return '{"error": "GEMINI_API_KEY not configured"}', "Error: No API key"

        client = genai.Client(api_key=api_key)

        # Upload video to Gemini File API
        print("📤 Uploading video to Gemini...")
        try:
            video_file = client.files.upload(file=video_path)
        except Exception as e:
            return json.dumps({"error": f"Video upload failed: {str(e)}"}), ""

        # Wait for processing
        print("⏳ Waiting for Gemini video processing...")
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = client.files.get(name=video_file.name)

        if video_file.state.name == "FAILED":
            return json.dumps({"error": "Video processing failed in Gemini"}), ""

        # --- STAGE 3: JSON Tactical Analysis ---
        json_prompt = f"""
You are an elite UEFA Pro License Football Analyst and Data Scientist.

**CRITICAL DATA CONTEXT:**
Use this CSV data as your absolute source of truth for timestamps and events:
<csv_data>
{csv_data}
</csv_data>

**OUTPUT FORMAT:** EXCLUSIVELY a raw, valid JSON array. No markdown.

**JSON SCHEMA REQUIREMENTS:**
For each distinct tactical phase, generate an object with the following keys:
1. "start_timestamp": "MM:SS" (The exact start time of the tactical phase)
2. "end_timestamp": "MM:SS" (The exact end time of the tactical phase)
3. "phase_of_play": (e.g., "Build-up", "Counter-Attack", "Defensive Transition")
4. "possession_team": (Color/Name of the attacking team)
5. "pitch_zone": (e.g., "Defensive Third - Central", "Zone 14", "Wide Channel")
6. "event_type": (e.g., "Vertical Pass", "Interception", "Line-Breaking Pass")
7. "tactical_description": Detailed narrative of the shape, defensive reaction, and movements of both teams.
8. "attacking_team_execution_rating": (1-10 scale)
9. "defending_team_execution_rating": (1-10 scale)
10. "key_tactical_insight": One sentence summarizing the core lesson or error for both teams.
11. "coach_actionable_advice": Direct, practical instructions for the coach.
12. "suggested_training_drill": A specific, named training ground drill.
"""

        try:
            print("🧠 Stage 3: Generating JSON tactical analysis...")
            response_json = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[video_file, json_prompt],
            )
            tactical_json = response_json.text

            # --- STAGE 4: Comprehensive Text Report ---
            print("⏳ Rate-limit pause (15s)...")
            time.sleep(15)

            text_prompt = f"""
You are the Head Coach's First Assistant.
You are analyzing the provided match video. You must also use the raw CSV timeline and the structured JSON tactical data we just extracted.

<csv_data>
{csv_data}
</csv_data>

<tactical_json>
{tactical_json}
</tactical_json>

Based strictly on your visual analysis combined with the CSV and JSON data, write a highly professional "Comprehensive Tactical Analysis" report in plain text (Markdown format). Use the video to add depth to the JSON findings.

Structure it EXACTLY like this template:

### Comprehensive Tactical Analysis ([Team A] vs. [Team B])
[Write a brief 2-sentence overarching summary of the match dynamics]

#### 1. [Title of First Tactical Observation based on the JSON and Video]
* **What the data says:** [Summarize start_timestamp, end_timestamp, event_type, and what happened using the CSV and Video]
* **Diagnosis:** [What went right/wrong based on the tactical_description and execution ratings]
* **Tactical Advice:** [Insert the coach_actionable_advice here, expanded slightly if the video provides more context]

[... repeat the above block for every phase found in the JSON ...]

---

### Training Tips for the Coach (Based on Data Analysis)

**1. Drill: "[Insert suggested_training_drill name]"**
* **Objective:** [What tactical flaw it fixes based on the key_tactical_insight]
* **The Drill:** [Explain how to run the drill]

[... repeat for all drills suggested in the JSON ...]

CRITICAL: Output ONLY the Markdown text. Do NOT wrap it in JSON. Be direct, authoritative, and analytical.
"""
            print("📝 Stage 4: Generating comprehensive text report...")
            response_text = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[video_file, text_prompt],
            )
            comprehensive_md = response_text.text

        except Exception as e:
            tactical_json = json.dumps({"error": str(e)})
            comprehensive_md = f"Error generating report: {str(e)}"
        finally:
            # Cleanup uploaded video from Google servers
            print("🗑️ Cleaning up Gemini video file...")
            try:
                client.files.delete(name=video_file.name)
            except Exception:
                pass

        return tactical_json, comprehensive_md

    # -------------------------------------------------------------------
    # HELPER: VIDEO DOWNLOAD
    # -------------------------------------------------------------------

    def _download_video(self, video_url: str) -> str:
        """Download a video to a temp file. Supports direct MP4 URLs and YouTube."""
        import subprocess

        output_path = f"/tmp/video_{uuid.uuid4().hex[:8]}.mp4"

        # Direct MP4 / non-YouTube URL: use curl, no yt-dlp needed
        youtube_hosts = ("youtube.com", "youtu.be")
        is_youtube = any(h in video_url for h in youtube_hosts)
        if not is_youtube:
            result = subprocess.run(
                ["curl", "-L", "--max-filesize", "500M", "-o", output_path, video_url],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(f"curl download failed: {result.stderr[:400]}")
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"Download produced no file: {output_path}")
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"📥 Downloaded video via curl: {size_mb:.1f} MB")
            return output_path

        base_cmd = [
            "yt-dlp",
            "-f", "best[height<=720]",  # Cap at 720p to save bandwidth
            "-o", output_path,
            "--no-playlist",
            "--quiet",
        ]

        # Build list of strategies to attempt in order.
        # Strategy 1: cookies file path from YOUTUBE_COOKIES_PATH env var (most reliable).
        #   To use: store your cookies.txt in a Modal Volume and set YOUTUBE_COOKIES_PATH.
        # Strategy 2: TV embedded client (bypasses bot detection without cookies).
        # Strategy 3: iOS client fallback.
        cookies_path = os.environ.get("YOUTUBE_COOKIES_PATH", "")
        strategies: list[list[str]] = []

        if cookies_path and os.path.exists(cookies_path):
            strategies.append(base_cmd + ["--cookies", cookies_path, video_url])

        strategies += [
            base_cmd + ["--extractor-args", "youtube:player_client=tv_embedded", video_url],
            base_cmd + ["--extractor-args", "youtube:player_client=ios", video_url],
            base_cmd + [video_url],  # last-resort: plain attempt
        ]

        last_error = ""
        for cmd in strategies:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                break
            last_error = result.stderr[:600]
            # Remove partial download before retrying
            if os.path.exists(output_path):
                os.remove(output_path)
        else:
            raise RuntimeError(f"yt-dlp failed after all strategies: {last_error}")

        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Video download failed: {output_path}")

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"📥 Downloaded video: {size_mb:.1f} MB")

        return output_path


# ---------------------------------------------------------------------------
# 3. WEB ENDPOINTS (Async Job Pattern)
# ---------------------------------------------------------------------------

@app.function(image=image, timeout=30)
@modal.fastapi_endpoint(method="POST", docs=True)
def submit(request: dict) -> dict:
    """
    Submit a video analysis job (async).
    Returns a job_id to poll for results.

    Request body:
    {
        "video_url": "https://youtube.com/watch?v=...",
        "inference_threshold": 0.3,    // optional
        "skip_gemini": false           // optional
    }
    """
    video_url = request.get("video_url", "")
    video_path = request.get("video_path", "")  # optional: path to file on the volume
    if not video_url and not video_path:
        return {"status": "error", "message": "video_url or video_path is required"}

    inference_threshold = request.get("inference_threshold", 0.3)
    skip_gemini = request.get("skip_gemini", False)

    # Spawn the GPU pipeline asynchronously
    service = CoachAIService()
    call = service.run_pipeline.spawn(
        video_url=video_url,
        inference_threshold=inference_threshold,
        skip_gemini=skip_gemini,
        video_path=video_path,
    )

    return {
        "status": "submitted",
        "job_id": call.object_id,
        "message": "Job submitted successfully. Poll GET /status?job_id=<job_id> for results.",
    }


@app.function(image=image, timeout=30)
@modal.fastapi_endpoint(method="GET", docs=True)
def status(job_id: str) -> dict:
    """
    Poll for the result of a submitted analysis job.

    Query param: ?job_id=<job_id>
    """
    import fastapi

    if not job_id:
        return {"status": "error", "message": "job_id query param is required"}

    try:
        function_call = modal.FunctionCall.from_id(job_id)
        result = function_call.get(timeout=0)
        return {"status": "completed", "result": result}
    except TimeoutError:
        return fastapi.responses.JSONResponse(
            content={"status": "pending", "message": "Job is still processing..."},
            status_code=202,
        )
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


# ---------------------------------------------------------------------------
# 4. OPTIONAL: Synchronous endpoint for short videos / testing
# ---------------------------------------------------------------------------

@app.function(
    image=image,
    gpu=["T4", "L4", "A10"],
    volumes={WEIGHTS_DIR: volume},
    secrets=[modal.Secret.from_name("gemini-api-key")],
    timeout=900,
)
@modal.fastapi_endpoint(method="POST", docs=True)
def analyze(request: dict) -> dict:
    """
    Synchronous analysis endpoint (for testing / short videos only).
    WARNING: May timeout for videos longer than ~3 minutes.

    Request body same as /submit.
    """
    import sys
    sys.path.insert(0, "/root/app")

    video_url = request.get("video_url")
    if not video_url:
        return {"status": "error", "message": "video_url is required"}

    # For the sync endpoint, we build a lightweight single-use pipeline
    # This is less efficient than the class-based approach but works for testing
    service = CoachAIService()
    return service.run_pipeline.remote(
        video_url=video_url,
        inference_threshold=request.get("inference_threshold", 0.3),
        skip_gemini=request.get("skip_gemini", False),
    )


# ---------------------------------------------------------------------------
# 5. HEALTH CHECK
# ---------------------------------------------------------------------------

@app.function(image=image, timeout=10)
@modal.fastapi_endpoint(method="GET", docs=True)
def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "CoachAI Video Analysis Agent",
        "models": MODELS_TO_RUN,
        "timestamp": datetime.utcnow().isoformat(),
    }
