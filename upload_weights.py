"""
One-time script to upload model checkpoints, configs, and class definitions
to a Modal Volume for persistent storage.

Usage:
    modal run upload_weights.py
"""

import modal
import os

volume = modal.Volume.from_name("coachAI-weights", create_if_missing=True)

app = modal.App("coachAI-upload")

# Mount the local directories we need to upload
local_mount = modal.Mount.from_local_dir(
    os.path.join(os.path.dirname(__file__), "checkpoints"),
    remote_path="/local_src/checkpoints",
)
config_mount = modal.Mount.from_local_dir(
    os.path.join(os.path.dirname(__file__), "config"),
    remote_path="/local_src/config",
)
data_mount = modal.Mount.from_local_dir(
    os.path.join(os.path.dirname(__file__), "data"),
    remote_path="/local_src/class_data",
)


@app.function(
    volumes={"/weights": volume},
    mounts=[local_mount, config_mount, data_mount],
    timeout=300,
)
def upload():
    import shutil

    # Upload checkpoints
    src_ckpt = "/local_src/checkpoints"
    dst_ckpt = "/weights/checkpoints"
    if os.path.exists(dst_ckpt):
        shutil.rmtree(dst_ckpt)
    shutil.copytree(src_ckpt, dst_ckpt)
    print(f"✅ Uploaded checkpoints -> {dst_ckpt}")

    # Upload configs
    src_cfg = "/local_src/config"
    dst_cfg = "/weights/config"
    if os.path.exists(dst_cfg):
        shutil.rmtree(dst_cfg)
    shutil.copytree(src_cfg, dst_cfg)
    print(f"✅ Uploaded configs -> {dst_cfg}")

    # Upload class definitions (renamed to class_data to avoid collision)
    src_data = "/local_src/class_data"
    dst_data = "/weights/class_data"
    if os.path.exists(dst_data):
        shutil.rmtree(dst_data)
    shutil.copytree(src_data, dst_data)
    print(f"✅ Uploaded class data -> {dst_data}")

    # Verify
    for root, dirs, files in os.walk("/weights"):
        level = root.replace("/weights", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        if level < 3:  # Don't go too deep
            subindent = " " * 2 * (level + 1)
            for file in files:
                fpath = os.path.join(root, file)
                size_mb = os.path.getsize(fpath) / (1024 * 1024)
                print(f"{subindent}{file} ({size_mb:.1f} MB)")

    volume.commit()
    print("\n🎉 All weights uploaded and committed to Modal Volume 'coachAI-weights'")
