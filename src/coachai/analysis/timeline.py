"""
Frame→timestamp conversion and JSON→CSV export.

Extracted from ``run_pipeline.py`` (``frame_to_time``, ``process_to_csv``)
and the corresponding logic in ``modal_app.py``.
"""

import json
import os

import pandas as pd

from coachai.config import FPS


def frame_to_time(frame: int, fps: int = FPS) -> str:
    """Convert a frame number to an ``MM:SS`` timestamp string."""
    total_seconds = int(frame) / fps
    return f"{int(total_seconds // 60):02d}:{int(total_seconds % 60):02d}"


def events_to_dataframe(events: list[dict], fps: int = FPS) -> pd.DataFrame:
    """Convert a list of event dicts (frame, label, confidence) to a DataFrame with timestamps."""
    if not events:
        return pd.DataFrame(columns=["frame", "timestamp", "label", "confidence"])

    df = pd.DataFrame(events)
    df["timestamp"] = df["frame"].apply(lambda f: frame_to_time(f, fps))
    cols = ["frame", "timestamp", "label", "confidence"]
    return df[[c for c in cols if c in df.columns]]


def inference_json_to_csv(
    json_path: str,
    csv_path: str,
    fps: int = FPS,
) -> None:
    """Read a ``results_inference.json`` file and write a CSV with timestamps."""
    with open(json_path, "r") as f:
        data = json.load(f)

    predictions = data.get("predictions", data)
    df = events_to_dataframe(predictions, fps)

    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
