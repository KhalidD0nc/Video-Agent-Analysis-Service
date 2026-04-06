"""
Gemini API wrapper for tactical video analysis.

Extracted from ``modal_app.py`` (``_run_gemini_analysis``) and the
equivalent function in ``run_pipeline.py`` / ``run_but_by_youtube.py``.
"""

import json
import os
import time

from coachai.config import (
    GEMINI_API_KEY_ENV,
    GEMINI_MODEL,
    GEMINI_RATE_LIMIT_PAUSE,
)
from coachai.reporting.prompts import json_tactical_prompt, text_report_prompt


def run_gemini_analysis(
    video_path: str,
    csv_data: str,
    api_key: str | None = None,
    model: str = GEMINI_MODEL,
    primary_team: str = "",
) -> tuple[str, str]:
    """Upload a video to Gemini and run the two-stage tactical analysis.

    Parameters
    ----------
    video_path:
        Local path to the video file.
    csv_data:
        The cleaned timeline CSV as a string.
    api_key:
        Gemini API key.  Falls back to the ``GEMINI_API_KEY`` env var.
    model:
        Gemini model name.

    Returns
    -------
    tactical_json:
        Raw JSON string from Stage 3.
    comprehensive_md:
        Markdown report from Stage 4.
    """
    from google import genai

    if api_key is None:
        api_key = os.environ.get(GEMINI_API_KEY_ENV)
    if not api_key:
        return json.dumps({"error": "GEMINI_API_KEY not configured"}), "Error: No API key"

    client = genai.Client(api_key=api_key)

    # Upload video
    try:
        video_file = client.files.upload(file=video_path)
    except Exception as e:
        return json.dumps({"error": f"Video upload failed: {e!s}"}), ""

    # Wait for processing
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name == "FAILED":
        return json.dumps({"error": "Video processing failed in Gemini"}), ""

    try:
        # Stage 3: JSON tactical analysis
        response_json = client.models.generate_content(
            model=model,
            contents=[video_file, json_tactical_prompt(csv_data, primary_team=primary_team)],
        )
        tactical_json = response_json.text

        # Rate-limit pause
        time.sleep(GEMINI_RATE_LIMIT_PAUSE)

        # Stage 4: Comprehensive text report
        response_text = client.models.generate_content(
            model=model,
            contents=[
                video_file,
                text_report_prompt(csv_data, tactical_json, primary_team=primary_team),
            ],
        )
        comprehensive_md = response_text.text

    except Exception as e:
        tactical_json = json.dumps({"error": str(e)})
        comprehensive_md = f"Error generating report: {e!s}"
    finally:
        try:
            client.files.delete(name=video_file.name)
        except Exception:
            pass

    return tactical_json, comprehensive_md
