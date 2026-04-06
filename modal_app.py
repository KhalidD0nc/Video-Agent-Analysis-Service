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

import os
from datetime import datetime
from pathlib import Path

import modal

# ---------------------------------------------------------------------------
# 1. APP & INFRASTRUCTURE
# ---------------------------------------------------------------------------

app = modal.App("coachAI-video-analysis")

volume = modal.Volume.from_name("coachAI-weights", create_if_missing=True)
WEIGHTS_DIR = Path("/weights")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1", "libglib2.0-0", "ffmpeg", "curl", "unzip")
    .run_commands(
        "curl -fsSL https://deno.land/install.sh | sh",
        "mv /root/.deno/bin/deno /usr/local/bin/deno",
    )
    .pip_install(
        "torch==2.5.1",
        "torchvision==0.20.1",
        "timm==1.0.24",
        "SoccerNet==0.1.62",
        "opencv-python-headless==4.13.0.92",
        "huggingface-hub==1.4.1",
        "numpy==2.3.5",
        "pandas==3.0.1",
        "scikit-learn==1.8.0",
        "scipy==1.17.0",
        "pillow==11.3.0",
        "tqdm==4.67.3",
        "tabulate==0.9.0",
        "PyYAML==6.0.3",
        "google-genai==1.64.0",
        "yt-dlp==2026.2.21",
        "python-dotenv==1.2.1",
        "fastapi[standard]",
    )
    .env({
        "WANDB_MODE": "offline",
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
    })
    # Source dirs baked in last (Modal v1 rule)
    .add_local_dir(os.path.join(os.path.dirname(__file__), "model"), remote_path="/root/app/model")
    .add_local_dir(os.path.join(os.path.dirname(__file__), "dataset"), remote_path="/root/app/dataset")
    .add_local_dir(os.path.join(os.path.dirname(__file__), "util"), remote_path="/root/app/util")
    .add_local_dir(os.path.join(os.path.dirname(__file__), "src"), remote_path="/root/app/src")
)


# ---------------------------------------------------------------------------
# 2. GPU SERVICE (persistent model loading)
# ---------------------------------------------------------------------------

@app.cls(
    image=image,
    gpu=["T4", "L4", "A10"],
    volumes={WEIGHTS_DIR: volume},
    secrets=[modal.Secret.from_name("gemini-api-key")],
    scaledown_window=300,
    min_containers=0,
    max_containers=3,
    timeout=900,
)
class CoachAIService:
    """Persistent GPU container — loads T-DEED models once, serves many requests."""

    @modal.enter()
    def load_models(self):
        import sys
        import torch

        sys.path.insert(0, "/root/app")
        sys.path.insert(0, "/root/app/src")

        from coachai.inference.engine import build_args, load_model
        from coachai.config import MODELS_TO_RUN

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Container booted on [{self.device.type.upper()}]")

        self.models, self.classes, self.configs = {}, {}, {}
        for model_name in MODELS_TO_RUN:
            model, classes, config = load_model(
                model_name, str(WEIGHTS_DIR), self.device
            )
            self.models[model_name] = model
            self.classes[model_name] = classes
            self.configs[model_name] = config
            print(f"Loaded {model_name}")

        print(f"All {len(self.models)} models ready")

    @modal.method()
    def run_pipeline(
        self,
        video_url: str = "",
        video_path: str = "",
        inference_threshold: float = 0.3,
        skip_gemini: bool = False,
    ) -> dict:
        import sys

        sys.path.insert(0, "/root/app")
        sys.path.insert(0, "/root/app/src")

        from coachai.pipeline import run

        preloaded = {
            name: (self.models[name], self.classes[name], self.configs[name])
            for name in self.models
        }
        return run(
            video_url=video_url,
            video_path=video_path,
            inference_threshold=inference_threshold,
            skip_gemini=skip_gemini,
            preloaded_models=preloaded,
            volume=volume,
        )


# ---------------------------------------------------------------------------
# 3. WEB ENDPOINTS
# ---------------------------------------------------------------------------

@app.function(image=image, timeout=30)
@modal.fastapi_endpoint(method="POST", docs=True)
def submit(request: dict) -> dict:
    """Submit a video analysis job (async). Returns job_id to poll."""
    video_url = request.get("video_url", "")
    video_path = request.get("video_path", "")
    if not video_url and not video_path:
        return {"status": "error", "message": "video_url or video_path is required"}

    call = CoachAIService().run_pipeline.spawn(
        video_url=video_url,
        inference_threshold=request.get("inference_threshold", 0.3),
        skip_gemini=request.get("skip_gemini", False),
        video_path=video_path,
    )
    return {
        "status": "submitted",
        "job_id": call.object_id,
        "message": "Poll GET /status?job_id=<job_id> for results.",
    }


@app.function(image=image, timeout=30)
@modal.fastapi_endpoint(method="GET", docs=True)
def status(job_id: str) -> dict:
    """Poll for job result by job_id."""
    import fastapi

    if not job_id:
        return {"status": "error", "message": "job_id is required"}
    try:
        result = modal.FunctionCall.from_id(job_id).get(timeout=0)
        return {"status": "completed", "result": result}
    except TimeoutError:
        return fastapi.responses.JSONResponse(
            content={"status": "pending", "message": "Job is still processing..."},
            status_code=202,
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.function(
    image=image,
    gpu=["T4", "L4", "A10"],
    volumes={WEIGHTS_DIR: volume},
    secrets=[modal.Secret.from_name("gemini-api-key")],
    timeout=900,
)
@modal.fastapi_endpoint(method="POST", docs=True)
def analyze(request: dict) -> dict:
    """Synchronous analysis (testing / short videos only)."""
    import sys
    sys.path.insert(0, "/root/app")

    video_url = request.get("video_url", "")
    if not video_url:
        return {"status": "error", "message": "video_url is required"}
    return CoachAIService().run_pipeline.remote(
        video_url=video_url,
        inference_threshold=request.get("inference_threshold", 0.3),
        skip_gemini=request.get("skip_gemini", False),
    )


@app.function(image=image, timeout=10)
@modal.fastapi_endpoint(method="GET", docs=True)
def health() -> dict:
    """Health check."""
    from coachai.config import MODELS_TO_RUN
    return {
        "status": "healthy",
        "service": "CoachAI Video Analysis Agent",
        "models": list(MODELS_TO_RUN),
        "timestamp": datetime.utcnow().isoformat(),
    }
