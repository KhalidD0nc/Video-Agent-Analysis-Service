"""
Video download helpers — supports direct URLs and YouTube.

Consolidates download logic from modal_app.py._download_video() and
run_but_by_youtube.download_youtube_video().
"""

import os
import subprocess
import uuid

from coachai.config import (
    DOWNLOAD_MAX_FILESIZE,
    DOWNLOAD_TIMEOUT,
    YOUTUBE_COOKIES_PATH_ENV,
    YOUTUBE_FORMAT,
)

YOUTUBE_HOSTS = ("youtube.com", "youtu.be")


def download_video(video_url: str, output_dir: str = "/tmp") -> str:
    """Download a video to *output_dir*. Returns the local file path.

    Dispatches to :func:`_download_direct` for plain URLs and
    :func:`_download_youtube` for YouTube links.
    """
    output_path = os.path.join(output_dir, f"video_{uuid.uuid4().hex[:8]}.mp4")

    if any(h in video_url for h in YOUTUBE_HOSTS):
        return _download_youtube(video_url, output_path)
    return _download_direct(video_url, output_path)


# ── Internal helpers ────────────────────────────────────────────────────────


def _download_direct(url: str, output_path: str) -> str:
    """Download a direct MP4 / non-YouTube URL via ``curl``."""
    result = subprocess.run(
        ["curl", "-L", "--max-filesize", DOWNLOAD_MAX_FILESIZE, "-o", output_path, url],
        capture_output=True,
        text=True,
        timeout=DOWNLOAD_TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl download failed: {result.stderr[:400]}")
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Download produced no file: {output_path}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Downloaded video via curl: {size_mb:.1f} MB")
    return output_path


def _download_youtube(url: str, output_path: str) -> str:
    """Download a YouTube video via ``yt-dlp`` with multi-strategy fallback."""
    base_cmd = [
        "yt-dlp",
        "-f",
        YOUTUBE_FORMAT,
        "-o",
        output_path,
        "--no-playlist",
        "--quiet",
    ]

    cookies_path = os.environ.get(YOUTUBE_COOKIES_PATH_ENV, "")
    strategies: list[list[str]] = []

    if cookies_path and os.path.exists(cookies_path):
        strategies.append(base_cmd + ["--cookies", cookies_path, url])

    strategies += [
        base_cmd + ["--extractor-args", "youtube:player_client=tv_embedded", url],
        base_cmd + ["--extractor-args", "youtube:player_client=ios", url],
        base_cmd + [url],
    ]

    last_error = ""
    for cmd in strategies:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=DOWNLOAD_TIMEOUT)
        if result.returncode == 0:
            break
        last_error = result.stderr[:600]
        if os.path.exists(output_path):
            os.remove(output_path)
    else:
        raise RuntimeError(f"yt-dlp failed after all strategies: {last_error}")

    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Video download failed: {output_path}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Downloaded video: {size_mb:.1f} MB")
    return output_path
