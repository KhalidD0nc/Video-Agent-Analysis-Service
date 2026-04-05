"""
upload_weights.py — Upload local model weights to Modal Volume
==============================================================

Uploads the local checkpoints/ and config/ directories into the
"coachAI-weights" Modal Volume so the inference container can load them.

Usage:
    modal run upload_weights.py

Modal v1 API Note:
    modal.Mount is REMOVED in Modal v1. Use modal.Volume + put_directory()
    or the `modal volume put` CLI command instead.
"""

import modal
import os

# The same Volume used by modal_app.py
volume = modal.Volume.from_name("coachAI-weights", create_if_missing=True)

app = modal.App("coachAI-upload-weights")

ROOT = os.path.dirname(os.path.abspath(__file__))


@app.function(
    volumes={"/weights": volume},
    # Give plenty of time for large checkpoint uploads
    timeout=1800,
)
def upload_weights():
    """
    Copies local directories into the Modal Volume.

    Directory layout inside the volume:
        /weights/
          checkpoints/
            SoccerNet/
              SoccerNet_small/
                checkpoint_best.pt
            SoccerNetBall/
              SoccerNetBall_challenge1/
                checkpoint_best.pt
          config/
            SoccerNet/
              SoccerNet_small.json
            SoccerNetBall/
              SoccerNetBall_challenge1.json
          class_data/
            soccernet/
              class.txt
            soccernetball/
              class.txt
    """
    import os
    import shutil

    volume_root = "/weights"

    # -----------------------------------------------------------------------
    # Local source directories (relative to this file)
    # -----------------------------------------------------------------------
    local_checkpoints = "/mnt/local/checkpoints"
    local_config      = "/mnt/local/config"
    local_class_data  = "/mnt/local/dataset"   # class.txt files live in dataset/

    def sync_dir(src: str, dst: str):
        """Copy every file from src into dst, preserving sub-tree structure."""
        if not os.path.exists(src):
            print(f"⚠️  Source directory not found, skipping: {src}")
            return 0

        count = 0
        for dirpath, _, filenames in os.walk(src):
            for fname in filenames:
                src_file = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(src_file, src)
                dst_file = os.path.join(dst, rel_path)
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copy2(src_file, dst_file)
                print(f"  ✅ {rel_path}")
                count += 1
        return count

    total = 0
    print("📦 Uploading checkpoints...")
    total += sync_dir(local_checkpoints, os.path.join(volume_root, "checkpoints"))

    print("📄 Uploading configs...")
    total += sync_dir(local_config, os.path.join(volume_root, "config"))

    print("🏷️  Uploading class data...")
    # Copy only class.txt files from dataset/
    total += sync_dir(local_class_data, os.path.join(volume_root, "class_data"))

    # Commit the changes so the volume reflects the new files
    volume.commit()

    print(f"\n✅ Upload complete — {total} files written to Volume.")


@app.local_entrypoint()
def main():
    """
    The recommended way to upload is via the Modal CLI:

        modal volume put coachAI-weights ./checkpoints /checkpoints
        modal volume put coachAI-weights ./config      /config
        modal volume put coachAI-weights ./dataset     /class_data

    This script provides a Python-based alternative using a mounted
    local directory approach via add_local_dir on a helper image.
    """
    print("=" * 60)
    print("CoachAI — Weight Upload Utility")
    print("=" * 60)
    print()
    print("ℹ️  modal.Mount was removed in Modal v1.")
    print("    The recommended approach is the Modal CLI:\n")
    print("    modal volume put coachAI-weights ./checkpoints /checkpoints")
    print("    modal volume put coachAI-weights ./config      /config")
    print("    modal volume put coachAI-weights ./dataset     /class_data")
    print()
    print("    Run those three commands and you're done!")
    print()
    print("    Alternatively, you can run the upload_weights function")
    print("    by adding a local dir mount — see the Modal docs for")
    print("    add_local_dir() on Image if you need a programmatic upload.")
