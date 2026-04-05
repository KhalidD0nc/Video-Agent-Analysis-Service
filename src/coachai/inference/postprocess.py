"""
Post-processing helpers for T-DEED inference output.

Extracted from ``util/eval.py``.  Contains:
- Frame-level prediction processing (score normalisation → event extraction)
- Non-Maximum Suppression (hard and soft variants)
"""

import copy
from collections import defaultdict

import numpy as np


# ── Frame prediction → event list ───────────────────────────────────────────

def process_frame_predictions(
    dataset, classes, pred_dict, high_recall_score_threshold=0.01
):
    """Convert per-frame score matrices into event lists (with eval stats)."""
    from util.score import compute_mAPs  # only needed for training eval

    classes_inv = {v: k for k, v in classes.items()}

    fps_dict = {}
    for video, _, fps in dataset.videos:
        fps_dict[video] = fps

    err = ErrorStat()
    f1 = ForegroundF1()

    pred_events = []
    pred_events_high_recall = []
    pred_scores = {}
    for video, (scores, support) in sorted(pred_dict.items()):
        label = dataset.get_labels(video)
        if np.min(support) == 0:
            support[support == 0] = 1
        assert np.min(support) > 0, (video, support.tolist())
        scores /= support[:, None]
        pred = np.argmax(scores, axis=1)
        err.update(label, pred)

        pred_scores[video] = scores.tolist()

        events = []
        events_high_recall = []
        for i in range(pred.shape[0]):
            f1.update(label[i], pred[i])

            if pred[i] != 0:
                events.append({
                    "label": classes_inv[pred[i]],
                    "frame": i,
                    "score": scores[i, pred[i]].item(),
                })

            for j in classes_inv:
                if scores[i, j] >= high_recall_score_threshold:
                    events_high_recall.append({
                        "label": classes_inv[j],
                        "frame": i,
                        "score": scores[i, j].item(),
                    })

        pred_events.append({
            "video": video, "events": events, "fps": fps_dict[video]
        })
        pred_events_high_recall.append({
            "video": video, "events": events_high_recall, "fps": fps_dict[video]
        })

    return err, f1, pred_events, pred_events_high_recall, pred_scores


def process_frame_predictions_challenge(
    dataset, classes, pred_dict, high_recall_score_threshold=0.05
):
    """Like :func:`process_frame_predictions` but without ground-truth labels."""
    classes_inv = {v: k for k, v in classes.items()}

    fps_dict = {}
    for video, _, fps in dataset.videos:
        fps_dict[video] = fps

    pred_events = []
    pred_events_high_recall = []
    pred_scores = {}
    for video, (scores, support) in sorted(pred_dict.items()):
        if np.min(support) == 0:
            support[support == 0] = 1
        assert np.min(support) > 0, (video, support.tolist())
        scores /= support[:, None]
        pred = np.argmax(scores, axis=1)

        pred_scores[video] = scores.tolist()

        events = []
        events_high_recall = []
        for i in range(pred.shape[0]):
            if pred[i] != 0:
                events.append({
                    "label": classes_inv[pred[i]],
                    "frame": i,
                    "score": scores[i, pred[i]].item(),
                })

            for j in classes_inv:
                if scores[i, j] >= high_recall_score_threshold:
                    events_high_recall.append({
                        "label": classes_inv[j],
                        "frame": i,
                        "score": scores[i, j].item(),
                    })

        pred_events.append({
            "video": video, "events": events, "fps": fps_dict[video]
        })
        pred_events_high_recall.append({
            "video": video, "events": events_high_recall, "fps": fps_dict[video]
        })

    return pred_events, pred_events_high_recall, pred_scores


def process_frame_predictions_inference(
    dataset, classes, scores, support, high_recall_score_threshold=0.05
):
    """Lightweight version for single-video inference (no dataset wrapper)."""
    classes_inv = {v: k for k, v in classes.items()}

    if np.min(support) == 0:
        support[support == 0] = 1
    assert np.min(support) > 0, support.tolist()
    scores /= support[:, None]
    pred = np.argmax(scores, axis=1)
    pred_scores = scores.tolist()

    events = []
    events_high_recall = []
    for i in range(pred.shape[0]):
        if pred[i] != 0:
            events.append({
                "label": classes_inv[pred[i]],
                "frame": i,
                "score": scores[i, pred[i]].item(),
            })

        for j in classes_inv:
            if scores[i, j] >= high_recall_score_threshold:
                events_high_recall.append({
                    "label": classes_inv[j],
                    "frame": i,
                    "score": scores[i, j].item(),
                })

    return events, events_high_recall, pred_scores


# ── Non-Maximum Suppression ──��─────────────────────────���────────────────────

def non_maximum_supression(pred, window, threshold=0.0):
    """Hard NMS: keep highest-scoring event, remove neighbours within *window*."""
    preds = copy.deepcopy(pred)
    new_pred = []
    for video_pred in preds:
        events_by_label = defaultdict(list)
        for e in video_pred["events"]:
            events_by_label[e["label"]].append(e)

        events = []
        i = 0
        for v in events_by_label.values():
            if type(window) is not list:
                class_window = window
            else:
                class_window = window[i]
                i += 1
            while len(v) > 0:
                e1 = max(v, key=lambda x: x["score"])
                if e1["score"] < threshold:
                    break
                pos1 = [
                    pos for pos, e in enumerate(v) if e["frame"] == e1["frame"]
                ][0]
                events.append(copy.deepcopy(e1))
                v.pop(pos1)
                list_pos = [
                    pos
                    for pos, e in enumerate(v)
                    if (e["frame"] >= e1["frame"] - class_window)
                    and (e["frame"] <= e1["frame"] + class_window)
                ]
                for pos in list_pos[::-1]:
                    v.pop(pos)

        events.sort(key=lambda x: x["frame"])
        new_video_pred = copy.deepcopy(video_pred)
        new_video_pred["events"] = events
        new_video_pred["num_events"] = len(events)
        new_pred.append(new_video_pred)
    return new_pred


def soft_non_maximum_supression(pred, window, threshold=0.01):
    """Soft NMS: decay scores of neighbours rather than removing them."""
    preds = copy.deepcopy(pred)
    new_pred = []
    for video_pred in preds:
        events_by_label = defaultdict(list)
        for e in video_pred["events"]:
            events_by_label[e["label"]].append(e)

        events = []
        i = 0
        for v in events_by_label.values():
            if type(window) is not list:
                class_window = window
            else:
                class_window = window[i]
                i += 1
            while len(v) > 0:
                e1 = max(v, key=lambda x: x["score"])
                if e1["score"] < threshold:
                    break
                pos1 = [
                    pos for pos, e in enumerate(v) if e["frame"] == e1["frame"]
                ][0]
                events.append(copy.deepcopy(e1))
                list_pos = [
                    pos
                    for pos, e in enumerate(v)
                    if (e["frame"] >= e1["frame"] - class_window)
                    and (e["frame"] <= e1["frame"] + class_window)
                ]
                for pos in list_pos:
                    v[pos]["score"] = (
                        v[pos]["score"]
                        * (np.abs(e1["frame"] - v[pos]["frame"])) ** 2
                        / ((class_window + 0) ** 2)
                    )
                v.pop(pos1)

        events.sort(key=lambda x: x["frame"])
        new_video_pred = copy.deepcopy(video_pred)
        new_video_pred["events"] = events
        new_video_pred["num_events"] = len(events)
        new_pred.append(new_video_pred)
    return new_pred


# ── Helper stat classes ─���─────────────────────────���─────────────────────────

class ErrorStat:

    def __init__(self):
        self._total = 0
        self._err = 0

    def update(self, true, pred):
        self._err += np.sum(true != pred)
        self._total += true.shape[0]

    def get(self):
        return self._err / self._total

    def get_acc(self):
        return 1.0 - self.get()


class ForegroundF1:

    def __init__(self):
        self._tp = defaultdict(int)
        self._fp = defaultdict(int)
        self._fn = defaultdict(int)

    def update(self, true, pred):
        if pred != 0:
            if true != 0:
                self._tp[None] += 1
            else:
                self._fp[None] += 1

            if pred == true:
                self._tp[pred] += 1
            else:
                self._fp[pred] += 1
                if true != 0:
                    self._fn[true] += 1
        elif true != 0:
            self._fn[None] += 1
            self._fn[true] += 1

    def get(self, k):
        return self._f1(k)

    def tp_fp_fn(self, k):
        return self._tp[k], self._fp[k], self._fn[k]

    def _f1(self, k):
        denom = self._tp[k] + 0.5 * self._fp[k] + 0.5 * self._fn[k]
        if denom == 0:
            assert self._tp[k] == 0
            denom = 1
        return self._tp[k] / denom
