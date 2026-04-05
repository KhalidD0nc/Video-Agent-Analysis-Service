"""Smoke tests — verify that the coachai package imports cleanly."""

import sys
import os

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_config_imports():
    from coachai.config import FPS, FRAME_SIZE, MODELS_TO_RUN
    assert FPS == 25
    assert FRAME_SIZE == (796, 448)
    assert len(MODELS_TO_RUN) == 2


def test_prompts_render():
    from coachai.reporting.prompts import json_tactical_prompt, text_report_prompt
    jp = json_tactical_prompt("fake,csv,data")
    assert "UEFA Pro License" in jp
    tp = text_report_prompt("csv", "json")
    assert "Head Coach" in tp


def test_io_helpers():
    from coachai.inference.io import load_text, DATASETS
    assert "soccernetv2" in DATASETS
    assert callable(load_text)


def test_timeline_frame_to_time():
    from coachai.analysis.timeline import frame_to_time
    assert frame_to_time(0) == "00:00"
    assert frame_to_time(75) == "00:03"   # 75 frames @ 25 fps = 3 sec
    assert frame_to_time(1500) == "01:00"  # 1500 / 25 = 60 sec


def test_cleaner_empty_input():
    from coachai.analysis.cleaner import merge_and_clean
    csv_str, events = merge_and_clean({})
    assert csv_str == ""
    assert events == []


def test_postprocess_nms_empty():
    from coachai.inference.postprocess import non_maximum_supression
    result = non_maximum_supression([{"events": [], "video": "test"}], window=3)
    assert len(result) == 1
    assert result[0]["events"] == []
