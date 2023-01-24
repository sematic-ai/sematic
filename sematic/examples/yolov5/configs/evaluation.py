# Standard Library
from dataclasses import dataclass


@dataclass
class EvaluationConfig:
    half: bool = True  # use FP16 half-precision inference
    augment: bool = False  # augmented inference
    conf_thres: float = 0.001  # confidence threshold
    iou_thres: float = 0.6  # NMS IoU threshold
    max_det: int = 300  # maximum detections per image
    single_cls: bool = False
