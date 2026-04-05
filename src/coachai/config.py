"""
Centralised configuration constants for the CoachAI pipeline.

Every magic number that was previously scattered across modal_app.py,
run_pipeline.py, run_but_by_youtube.py, inference.py, dataset/, and util/
now lives here.  Import from ``coachai.config`` instead of hard-coding.
"""

from pathlib import Path

# ── Video Processing ────────────────────────────────────────────────────────
FPS = 25
FRAME_WIDTH = 796
FRAME_HEIGHT = 448
FRAME_SIZE = (FRAME_WIDTH, FRAME_HEIGHT)
DEFAULT_PAD_LEN = 5

# ── Strides (frame down-sampling per dataset) ──────────────────────────────
STRIDE_DEFAULT = 1
STRIDE_SOCCERNET = 12
STRIDE_SOCCERNETBALL = 2

STRIDE_MAP = {
    "soccernet": STRIDE_SOCCERNET,
    "soccernetball": STRIDE_SOCCERNETBALL,
}

# ── Clip Overlap ────────────────────────────────────────────────────────────
OVERLAP_DEFAULT = 0.9
OVERLAP_SOCCERNET = 0.5

# ── NMS / Evaluation Windows & Tolerances ───────────────────────────────────
TOLERANCES = [1, 2, 4]
WINDOWS = [1, 3]
TOLERANCES_SN = [3, 6]
WINDOWS_SN = [3, 6]
TOLERANCES_SNB = [6, 12]
WINDOWS_SNB = [6, 12]
WINDOWS_T = [1, 3]
WINDOWS_FG = [1, 3]

WINDOWS_MAP = {
    "soccernet": WINDOWS_SN,
    "soccernetball": WINDOWS_SNB,
}

# ── Inference Thresholds ────────────────────────────────────────────────────
INFERENCE_THRESHOLD = 0.3
INFERENCE_BATCH_SIZE = 4

# ── Models ──────────────────────────────────────────────────────────────────
MODELS_TO_RUN = ["SoccerNet_small", "SoccerNetBall_challenge1"]
GEMINI_MODEL = "gemini-3-flash-preview"

# ── Output Directories ──────────────────────────────────────────────────────
CSV_OUT_DIR = "results_in_csv"
JSON_OUT_DIR = "inference_output"
FINAL_OUT_DIR = "final_output"

# ── Environment Variable Names ──────────────────────────────────────────────
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
YOUTUBE_COOKIES_PATH_ENV = "YOUTUBE_COOKIES_PATH"

# ── Runtime Environment ─────────────────────────────────────────────────────
PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True"
WANDB_MODE = "offline"

# ── Video Download ──────────────────────────────────────────────────────────
YOUTUBE_FORMAT = "best[height<=720]"
DOWNLOAD_MAX_FILESIZE = "500M"
DOWNLOAD_TIMEOUT = 120  # seconds

# ── Gemini API ──────────────────────────────────────────────────────────────
GEMINI_RATE_LIMIT_PAUSE = 15  # seconds between API calls

# ── Event Deduplication ─────────────────────────────────────────────────────
DEDUP_WINDOW_SECONDS = 3
DEDUP_WINDOW_FRAMES = FPS * DEDUP_WINDOW_SECONDS  # 75

# ── Modal Infrastructure (only used by modal_app.py) ────────────────────────
MODAL_WEIGHTS_DIR = Path("/weights")
MODAL_GPU_TYPES = ["T4", "L4", "A10"]
MODAL_SCALEDOWN_WINDOW = 300     # seconds
MODAL_MIN_CONTAINERS = 0
MODAL_MAX_CONTAINERS = 3
MODAL_TIMEOUT = 900              # seconds (15 min)

# ── Supported Datasets ──────────────────────────────────────────────────────
SUPPORTED_DATASETS = [
    "tennis",
    "fs_perf",
    "fs_comp",
    "finediving",
    "finegym",
    "soccernetv2",
    "soccernetball",
]
