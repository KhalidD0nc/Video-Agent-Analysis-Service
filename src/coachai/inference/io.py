"""
I/O helpers for loading and storing inference results.

Consolidates ``util/io.py`` and ``util/dataset.py`` into one module.
Original files are kept until all consumers are migrated.
"""

import json
import os

from coachai.config import FPS

# ── JSON helpers ────────────────────────────────────────────────────────────


def load_json(fpath):
    with open(fpath) as fp:
        return json.load(fp)


def store_json(fpath, obj, pretty=False):
    kwargs = {}
    if pretty:
        kwargs["indent"] = 2
        kwargs["sort_keys"] = True
    with open(fpath, "w") as fp:
        json.dump(obj, fp, **kwargs)


# ── Text helpers ────────────────────────────────────────────────────────────


def load_text(fpath):
    lines = []
    with open(fpath) as fp:
        for line in fp:
            line = line.strip()
            if line:
                lines.append(line)
    return lines


# ── Dataset helpers (from util/dataset.py) ──────────────────────────────────

DATASETS = [
    "tennis",
    "fs_perf",
    "fs_comp",
    "finediving",
    "finegym",
    "soccernetv2",
    "soccernetball",
]


def load_classes(file_name):
    return {x: i + 1 for i, x in enumerate(load_text(file_name))}


def read_fps(video_frame_dir):
    with open(os.path.join(video_frame_dir, "fps.txt")) as fp:
        return float(fp.read())


# ── SoccerNet JSON export ───────────────────────────────────────────────────


def store_json_sn(pred_path, pred, stride=1):
    i = 0
    for game in pred:
        if i % 2 == 0:
            gameDict = dict()
            gameDict["UrlLocal"] = game["video"]
            gameDict["predictions"] = []
        for event in game["events"]:
            eventDict = dict()
            position = int(event["frame"] / FPS * 1000 * stride)
            eventDict["gameTime"] = (
                f"{(i % 2) + 1} - {position // 60000}:{int((position % 60000) // 1000)}"
            )
            eventDict["label"] = event["label"]
            eventDict["position"] = position
            eventDict["confidence"] = event["score"]
            eventDict["half"] = (i % 2) + 1
            gameDict["predictions"].append(eventDict)

        if (i % 2) == 1:
            path = os.path.join(
                "/".join(pred_path.split("/")[:-1]) + "/preds",
                "/".join(game["video"].split("/")[:-1]),
            )
            if not os.path.exists(path):
                os.makedirs(path)
            with open(path + "/results_spotting.json", "w") as fp:
                json.dump(gameDict, fp, indent=4)

        i += 1


def store_json_snb(pred_path, pred, stride=1):
    for game in pred:
        gameDict = dict()
        gameDict["UrlLocal"] = game["video"]
        gameDict["predictions"] = []
        for event in game["events"]:
            eventDict = dict()
            position = int(event["frame"] / FPS * 1000 * stride)
            eventDict["gameTime"] = f"1 - {position // 60000}:{int((position % 60000) // 1000)}"
            eventDict["label"] = event["label"]
            eventDict["position"] = position
            eventDict["confidence"] = event["score"]
            eventDict["half"] = 1
            gameDict["predictions"].append(eventDict)

        path = os.path.join("/".join(pred_path.split("/")[:-1]) + "/preds", game["video"])
        if not os.path.exists(path):
            os.makedirs(path)
        with open(path + "/results_spotting.json", "w") as fp:
            json.dump(gameDict, fp, indent=4)


def store_json_inference(out_path, pred, stride=1):
    predDict = dict()
    predDict["predictions"] = []
    for event in pred["events"]:
        eventDict = dict()
        frame = int(event["frame"]) * stride
        eventDict["frame"] = frame
        eventDict["label"] = event["label"]
        eventDict["confidence"] = event["score"]
        predDict["predictions"].append(eventDict)

    if not os.path.exists(out_path):
        os.makedirs(out_path)
    with open(out_path + "/results_inference.json", "w") as fp:
        json.dump(predDict, fp, indent=4)
