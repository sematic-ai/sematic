# Standard Library
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, List, Tuple, Type, Union

# Third-party
import torch.nn

# Sematic
# YOLOv5
import sematic.examples.yolov5.models.common as models
from sematic.examples.yolov5.models.yolo import Detect


@dataclass
class ModelConfig:
    nc: int
    depth_multiple: float
    width_multiple: float
    anchors: List[Tuple[int, int, int, int, int, int]]
    backbone: List[Tuple[int, int, str, List[object]]]
    head: List[Tuple[Union[int, List[int]], int, str, List[object]]]
    freeze: List[int] = field(default_factory=lambda: [0])


YOLOV5L = ModelConfig(
    nc=80,
    depth_multiple=1.0,
    width_multiple=1.0,
    anchors=[
        [10, 13, 16, 30, 33, 23],  # P3/8
        [30, 61, 62, 45, 59, 119],  # P4/16
        [116, 90, 156, 198, 373, 326],  # P5/32
    ],
    backbone=[
        [-1, 1, "Conv", [64, 6, 2, 2]],  # 0-P1/2
        [-1, 1, "Conv", [128, 3, 2]],  # 1-P2/4
        [-1, 3, "C3", [128]],
        [-1, 1, "Conv", [256, 3, 2]],  # 3-P3/8
        [-1, 6, "C3", [256]],
        [-1, 1, "Conv", [512, 3, 2]],  # 5-P4/16
        [-1, 9, "C3", [512]],
        [-1, 1, "Conv", [1024, 3, 2]],  # 7-P5/32
        [-1, 3, "C3", [1024]],
        [-1, 1, "SPPF", [1024, 5]],  # 9
    ],
    head=[
        [-1, 1, "Conv", [512, 1, 1]],
        [-1, 1, "nn.Upsample", [None, 2, "nearest"]],
        [[-1, 6], 1, "Concat", [1]],  # cat backbone P4
        [-1, 3, "C3", [512, False]],  # 13
        [-1, 1, "Conv", [256, 1, 1]],
        [-1, 1, "nn.Upsample", [None, 2, "nearest"]],
        [[-1, 4], 1, "Concat", [1]],  # cat backbone P3
        [-1, 3, "C3", [256, False]],  # 17 (P3/8-small)
        [-1, 1, "Conv", [256, 3, 2]],
        [[-1, 14], 1, "Concat", [1]],  # cat head P4
        [-1, 3, "C3", [512, False]],  # 20 (P4/16-medium)
        [-1, 1, "Conv", [512, 3, 2]],
        [[-1, 10], 1, "Concat", [1]],  # cat head P5
        [-1, 3, "C3", [1024, False]],  # 23 (P5/32-large)
        [[17, 20, 23], 1, "Detect", ["nc", "anchors"]],  # Detect(P3, P4, P5)
    ],
)
