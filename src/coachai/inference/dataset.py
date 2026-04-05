"""
Inference-time dataset for streaming video frames into T-DEED.

Extracted from ``dataset/frame.py``.  Only the classes needed at
inference time live here — training datasets remain in ``dataset/``.
"""

from collections import deque

import cv2
import numpy as np
import torch
from torch.utils.data import IterableDataset

from coachai.config import DEFAULT_PAD_LEN, FRAME_SIZE


class ActionSpotInferenceDataset(IterableDataset):
    """Streams fixed-length clips from a video file for inference."""

    def __init__(
        self,
        video_path,
        clip_len,
        overlap_len=0,
        stride=1,
        pad_len=DEFAULT_PAD_LEN,
        dataset="finediving",
        size=FRAME_SIZE,
    ):
        self.video_path = video_path
        self._clip_len = clip_len
        self._overlap_len = self._clip_len - overlap_len
        self._stride = stride
        self._pad_len = pad_len
        self._dataset = dataset
        self._size = size
        stream = cv2.VideoCapture(self.video_path)
        self._video_len = int(stream.get(cv2.CAP_PROP_FRAME_COUNT))
        stream.release()

    def __iter__(self):
        stream = cv2.VideoCapture(self.video_path)
        buffer = deque()

        i = -self._pad_len * self._stride
        while True:
            if i < 0:
                if i % self._stride == 0:
                    frame = np.zeros(
                        (self._size[1], self._size[0], 3), np.uint8
                    )
                    frame = torch.from_numpy(frame).permute(2, 0, 1)
                    buffer.append(frame)
                i += 1
                continue

            ret, frame = stream.read()
            if not ret:
                break

            if i % self._stride != 0:
                i += 1
                continue

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, self._size)
            frame = torch.from_numpy(frame).permute(2, 0, 1)

            buffer.append(frame)
            i += 1

            if len(buffer) == self._clip_len:
                yield (
                    torch.stack(list(buffer)),
                    (i + self._stride - 1) // self._stride - self._clip_len,
                )
                for _ in range(self._overlap_len):
                    buffer.popleft()

        stream.release()
