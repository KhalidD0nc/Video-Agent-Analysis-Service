#!/usr/bin/env python3
"""
Thin CLI wrapper around the CoachAI pipeline.

Usage:
    python run_local.py --video_path match.mp4 --weights_dir ./weights
    python run_local.py --video_url "https://youtu.be/..." --skip_gemini
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Ensure src/ is on the path so ``coachai`` can be imported.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from coachai.config import FINAL_OUT_DIR, INFERENCE_THRESHOLD
from coachai.pipeline import run


def main():
    parser = argparse.ArgumentParser(description="CoachAI — local pipeline runner")
    parser.add_argument("--video_path", type=str, default="", help="Path to a local video file")
    parser.add_argument("--video_url", type=str, default="", help="URL to download video from")
    parser.add_argument(
        "--weights_dir", type=str, default="weights", help="Directory with model weights"
    )
    parser.add_argument("--inference_threshold", type=float, default=INFERENCE_THRESHOLD)
    parser.add_argument("--skip_gemini", action="store_true", help="Skip Gemini analysis stages")
    args = parser.parse_args()

    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    os.environ.setdefault("WANDB_MODE", "offline")

    results = run(
        video_url=args.video_url,
        video_path=args.video_path,
        weights_dir=args.weights_dir,
        inference_threshold=args.inference_threshold,
        skip_gemini=args.skip_gemini,
    )

    # Save outputs
    os.makedirs(FINAL_OUT_DIR, exist_ok=True)

    if results.get("timeline_csv"):
        csv_path = os.path.join(FINAL_OUT_DIR, "timeline.csv")
        with open(csv_path, "w") as f:
            f.write(results["timeline_csv"])
        print(f"Timeline saved to {csv_path}")

    if results.get("tactical_report_json"):
        json_path = os.path.join(FINAL_OUT_DIR, "tactical_report.json")
        with open(json_path, "w") as f:
            f.write(results["tactical_report_json"])
        print(f"Tactical JSON saved to {json_path}")

    if results.get("comprehensive_analysis_md"):
        md_path = os.path.join(FINAL_OUT_DIR, "analysis.md")
        with open(md_path, "w") as f:
            f.write(results["comprehensive_analysis_md"])
        print(f"Analysis report saved to {md_path}")

    print(f"\nPipeline completed in {results['pipeline_duration_seconds']}s")
    print(json.dumps(results["stages"], indent=2))


if __name__ == "__main__":
    main()
