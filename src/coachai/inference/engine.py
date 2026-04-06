"""
T-DEED inference engine — load models and run single-video inference.

Extracted from ``modal_app.py`` (``CoachAIService.load_models``,
``_build_args``, ``_run_inference``) and the ``inference()`` function in
``util/eval.py``.
"""

import argparse

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from coachai.config import (
    FRAME_SIZE,
    STRIDE_MAP,
    WINDOWS,
    WINDOWS_MAP,
)
from coachai.inference.dataset import ActionSpotInferenceDataset
from coachai.inference.io import load_classes, load_json
from coachai.inference.postprocess import (
    process_frame_predictions_inference,
    soft_non_maximum_supression,
)


def build_args(model_name: str, config: dict, device: torch.device) -> argparse.Namespace:
    """Build an ``argparse.Namespace`` from a config dict (mirrors ``update_args``)."""
    args = argparse.Namespace()
    args.model = model_name
    args.frame_dir = config["frame_dir"]
    args.save_dir = config.get("save_dir", "/tmp")
    args.store_dir = config.get("store_dir", "/tmp")
    args.store_mode = config["store_mode"]
    args.batch_size = config["batch_size"]
    args.clip_len = config["clip_len"]
    args.crop_dim = config["crop_dim"]
    if args.crop_dim <= 0:
        args.crop_dim = None
    args.dataset = config["dataset"]
    args.radi_displacement = config["radi_displacement"]
    args.epoch_num_frames = config["epoch_num_frames"]
    args.feature_arch = config["feature_arch"]
    args.learning_rate = config["learning_rate"]
    args.mixup = config["mixup"]
    args.modality = config["modality"]
    args.num_classes = config["num_classes"]
    args.num_epochs = config["num_epochs"]
    args.warm_up_epochs = config["warm_up_epochs"]
    args.start_val_epoch = config["start_val_epoch"]
    args.temporal_arch = config["temporal_arch"]
    args.n_layers = config["n_layers"]
    args.sgp_ks = config["sgp_ks"]
    args.sgp_r = config["sgp_r"]
    args.only_test = config["only_test"]
    args.criterion = config["criterion"]
    args.num_workers = config["num_workers"]
    args.pretrain = config.get("pretrain")
    args.device = device
    args.acc_grad_iter = 1
    args.seed = 1
    return args


def load_model(
    model_name: str,
    weights_dir: str,
    device: torch.device | None = None,
):
    """Load a single T-DEED model from *weights_dir* and return ``(model, classes, config)``."""
    from model.model import TDEEDModel

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    config_path = model_name.split("_")[0] + "/" + model_name + ".json"
    config = load_json(f"{weights_dir}/config/{config_path}")

    args = build_args(model_name, config, device)

    dataset_name = config["dataset"]
    classes = load_classes(f"{weights_dir}/class_data/{dataset_name}/class.txt")

    model = TDEEDModel(device=device, args=args)

    if args.pretrain is not None:
        pretrain_classes = load_classes(
            f"{weights_dir}/class_data/{args.pretrain['dataset']}/class.txt"
        )
        n_classes = [len(classes) + 1, len(pretrain_classes) + 1]
        model._model.update_pred_head(n_classes)
        model._num_classes = np.array(n_classes).sum()

    checkpoint_path = (
        f"{weights_dir}/checkpoints/{model_name.split('_')[0]}/{model_name}/checkpoint_best.pt"
    )
    model.load(torch.load(checkpoint_path, map_location=device))

    return model, classes, config


def run_inference(
    model,
    classes: dict,
    config: dict,
    video_path: str,
    threshold: float = 0.3,
    device: torch.device | None = None,
) -> list[dict]:
    """Run a single T-DEED model on *video_path* and return a list of event dicts.

    Each event dict has keys ``frame``, ``label``, and ``confidence``.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    stride = STRIDE_MAP.get(config["dataset"], 1)
    windows = WINDOWS_MAP.get(config["dataset"], WINDOWS)

    clip_len = config["clip_len"]
    inference_dataset = ActionSpotInferenceDataset(
        video_path,
        clip_len=clip_len,
        overlap_len=(clip_len // 4 * 3) if config["dataset"] != "soccernet" else (clip_len // 2),
        stride=stride,
        dataset=config["dataset"],
        size=FRAME_SIZE,
    )

    inference_loader = DataLoader(
        inference_dataset,
        batch_size=1,
        shuffle=False,
        num_workers=0,
        pin_memory=device.type == "cuda",
        drop_last=False,
    )

    video_len = inference_dataset._video_len

    predictions = np.zeros((video_len // stride, len(classes) + 1), np.float32)
    support = np.zeros(video_len // stride, np.int32)

    for frames, starts in tqdm(inference_loader, desc="Inference"):
        _, batch_pred_scores = model.predict(frames)

        for i in range(frames.shape[0]):
            pred_scores = batch_pred_scores[i]
            start = starts[i].item()
            if start < 0:
                pred_scores = pred_scores[-start:, :]
                start = 0
            end = start + pred_scores.shape[0]
            if end >= predictions.shape[0]:
                end = predictions.shape[0]
                pred_scores = pred_scores[: end - start, :]

            predictions[start:end, :] += pred_scores
            support[start:end] += (pred_scores.sum(axis=1) != 0) * 1

    _, pred_events_high_recall, _ = process_frame_predictions_inference(
        config["dataset"],
        classes,
        predictions,
        support,
        high_recall_score_threshold=threshold,
    )

    pred_events_nms = soft_non_maximum_supression(
        [{"events": pred_events_high_recall}],
        window=windows[1],
        threshold=threshold,
    )

    events = []
    for event in pred_events_nms[0]["events"]:
        events.append(
            {
                "frame": int(event["frame"]) * stride,
                "label": event["label"],
                "confidence": round(float(event["score"]), 4),
            }
        )

    return events
