"""
CoachAI pipeline orchestrator.

Ties together video download → T-DEED inference → cleaning → Gemini analysis
into a single ``run()`` function.  This is the only entry point that
``modal_app.py`` and ``run_local.py`` need to call.
"""

import os
import time

from coachai.analysis.cleaner import merge_and_clean
from coachai.config import MODELS_TO_RUN
from coachai.inference.engine import load_model, run_inference
from coachai.ingestion.downloader import download_video
from coachai.reporting.gemini_client import run_gemini_analysis


def run(
    video_url: str = "",
    video_path: str = "",
    weights_dir: str = "/weights",
    inference_threshold: float = 0.3,
    skip_gemini: bool = False,
    models: list[str] | None = None,
) -> dict:
    """Execute the full CoachAI pipeline.

    Parameters
    ----------
    video_url:
        URL to download the video from (direct or YouTube).
    video_path:
        Path to a local video file (skips download if provided).
    weights_dir:
        Directory containing model weights, configs, and class files.
    inference_threshold:
        Confidence threshold for event detection.
    skip_gemini:
        If ``True``, skip Stages 3–4 (Gemini analysis).
    models:
        List of model names to run.  Defaults to :data:`MODELS_TO_RUN`.

    Returns
    -------
    dict with keys: ``status``, ``stages``, ``timeline_csv``,
    ``tactical_report_json``, ``comprehensive_analysis_md``,
    ``pipeline_duration_seconds``.
    """
    import torch

    if models is None:
        models = list(MODELS_TO_RUN)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pipeline_start = time.time()
    results: dict = {"status": "success", "stages": {}}

    # ── Stage 0: Get video ──────────────────────────────────────────────
    stage_start = time.time()
    if video_path:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"video_path not found: {video_path}")
    else:
        if not video_url:
            raise ValueError("Either video_url or video_path must be provided")
        video_path = download_video(video_url)
    results["stages"]["download"] = {
        "duration_seconds": round(time.time() - stage_start, 1),
    }

    # ── Stage 1: T-DEED inference ───────────────────────────────────────
    stage_start = time.time()
    all_events: dict[str, list[dict]] = {}
    for model_name in models:
        model, classes, config = load_model(model_name, weights_dir, device)
        events = run_inference(
            model, classes, config, video_path,
            threshold=inference_threshold, device=device,
        )
        all_events[model_name] = events
        print(f"{model_name}: detected {len(events)} events")

    results["stages"]["inference"] = {
        "duration_seconds": round(time.time() - stage_start, 1),
        "events_per_model": {k: len(v) for k, v in all_events.items()},
    }

    # ── Stage 2: Merge & clean ──────────────────────────────────────────
    stage_start = time.time()
    timeline_csv, clean_events = merge_and_clean(all_events)
    results["stages"]["cleaning"] = {
        "duration_seconds": round(time.time() - stage_start, 1),
        "events_after_cleaning": len(clean_events),
    }
    results["timeline_csv"] = timeline_csv
    print(f"Cleaned timeline: {len(clean_events)} unique events")

    # ── Stages 3 & 4: Gemini analysis ───────────────────────────────────
    if not skip_gemini:
        stage_start = time.time()
        tactical_json, comprehensive_md = run_gemini_analysis(
            video_path, timeline_csv
        )
        results["stages"]["gemini_analysis"] = {
            "duration_seconds": round(time.time() - stage_start, 1),
        }
        results["tactical_report_json"] = tactical_json
        results["comprehensive_analysis_md"] = comprehensive_md

    results["pipeline_duration_seconds"] = round(time.time() - pipeline_start, 1)
    return results
