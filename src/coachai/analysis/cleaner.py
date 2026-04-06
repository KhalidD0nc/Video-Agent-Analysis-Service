"""
Merge and deduplicate events from multiple T-DEED models.

Extracted from ``modal_app.py`` (``_merge_and_clean``) and
``run_pipeline.py`` (``merge_and_clean_data``).
"""

import pandas as pd

from coachai.analysis.timeline import frame_to_time
from coachai.config import DEDUP_WINDOW_FRAMES, FPS

MODEL_EVENT_TYPE = {
    "SoccerNet_small": "Match Event",
    "SoccerNetBall_challenge1": "Ball Action",
}


def merge_and_clean(
    all_events: dict[str, list[dict]],
    fps: int = FPS,
    dedup_window: int = DEDUP_WINDOW_FRAMES,
) -> tuple[str, list[dict]]:
    """Merge events from multiple models and deduplicate within a time window.

    Parameters
    ----------
    all_events:
        ``{model_name: [{"frame", "label", "confidence"}, ...]}``
    fps:
        Frames per second (used for timestamp conversion).
    dedup_window:
        Max frame distance to consider events duplicates.

    Returns
    -------
    csv_string:
        The cleaned timeline as a CSV string.
    clean_events:
        List of event dicts.
    """
    rows: list[dict] = []
    for model_name, events in all_events.items():
        event_type = MODEL_EVENT_TYPE.get(model_name, model_name)
        for e in events:
            rows.append(
                {
                    "frame": e["frame"],
                    "timestamp": frame_to_time(e["frame"], fps),
                    "label": e["label"],
                    "confidence": e["confidence"],
                    "Event_Type": event_type,
                }
            )

    if not rows:
        return "", []

    df = pd.DataFrame(rows)
    df = df.sort_values(by=["label", "frame"])

    # Deduplication: within each label, group events that are within
    # *dedup_window* frames of each other and keep the highest-confidence one.
    df["frame_diff"] = df.groupby("label")["frame"].diff()
    df["event_block"] = (df["frame_diff"].fillna(dedup_window + 1) > dedup_window).cumsum()
    best_indices = df.groupby(["label", "event_block"])["confidence"].idxmax()

    df_clean = df.loc[best_indices].copy()
    df_clean = df_clean.sort_values(by="frame")
    df_clean = df_clean[["timestamp", "frame", "label", "confidence", "Event_Type"]]
    df_clean["confidence"] = df_clean["confidence"].apply(lambda x: round(x, 2))

    csv_string = df_clean.to_csv(index=False)
    clean_events = df_clean.to_dict(orient="records")
    return csv_string, clean_events
