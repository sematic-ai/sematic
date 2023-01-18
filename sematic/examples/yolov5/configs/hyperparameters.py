# Standard Library
from dataclasses import dataclass
from typing import Optional


@dataclass
class HyperParametersConfig:
    lr0: float  # initial learning rate (SGD=1E-2, Adam=1E-3)
    lrf: float  # final OneCycleLR learning rate (lr0 * lrf)
    momentum: float  # SGD momentum/Adam beta1
    weight_decay: float  # optimizer weight decay 5e-4
    warmup_epochs: float  # warmup epochs (fractions ok)
    warmup_momentum: float  # warmup initial momentum
    warmup_bias_lr: float  # warmup initial bias lr
    box: float  # box loss gain
    cls: float  # cls loss gain
    cls_pw: float  # cls BCELoss positive_weight
    obj: float  # obj loss gain (scale with pixels)
    obj_pw: float  # obj BCELoss positive_weight
    iou_t: float  # IoU training threshold
    anchor_t: float  # anchor-multiple threshold
    # anchors: 3  # anchors per output layer (0 to ignore)
    fl_gamma: float  # focal loss gamma (efficientDet default gamma=1.5)
    hsv_h: float  # image HSV-Hue augmentation (fraction)
    hsv_s: float  # image HSV-Saturation augmentation (fraction)
    hsv_v: float  # image HSV-Value augmentation (fraction)
    degrees: float  # image rotation (+/- deg)
    translate: float  # image translation (+/- fraction)
    scale: float  # image scale (+/- gain)
    shear: float  # image shear (+/- deg)
    perspective: float  # image perspective (+/- fraction), range 0-0.001
    flipud: float  # image flip up-down (probability)
    fliplr: float  # image flip left-right (probability)
    mosaic: float  # image mosaic (probability)
    mixup: float  # image mixup (probability)
    copy_paste: float  # segment copy-paste (probability)
    label_smoothing: float = 0.0
    anchors: Optional[float] = None


SCRATCH_LOW = HyperParametersConfig(
    lr0=0.01,  # initial learning rate (SGD=1E-2, Adam=1E-3)
    lrf=0.01,  # final OneCycleLR learning rate (lr0 * lrf)
    momentum=0.937,  # SGD momentum/Adam beta1
    weight_decay=0.0005,  # optimizer weight decay 5e-4
    warmup_epochs=3.0,  # warmup epochs (fractions ok)
    warmup_momentum=0.8,  # warmup initial momentum
    warmup_bias_lr=0.1,  # warmup initial bias lr
    box=0.05,  # box loss gain
    cls=0.5,  # cls loss gain
    cls_pw=1.0,  # cls BCELoss positive_weight
    obj=1.0,  # obj loss gain (scale with pixels)
    obj_pw=1.0,  # obj BCELoss positive_weight
    iou_t=0.20,  # IoU training threshold
    anchor_t=4.0,  # anchor-multiple threshold
    # anchors: 3  # anchors per output layer (0 to ignore)
    fl_gamma=0.0,  # focal loss gamma (efficientDet default gamma=1.5)
    hsv_h=0.015,  # image HSV-Hue augmentation (fraction)
    hsv_s=0.7,  # image HSV-Saturation augmentation (fraction)
    hsv_v=0.4,  # image HSV-Value augmentation (fraction)
    degrees=0.0,  # image rotation (+/- deg)
    translate=0.1,  # image translation (+/- fraction)
    scale=0.5,  # image scale (+/- gain)
    shear=0.0,  # image shear (+/- deg)
    perspective=0.0,  # image perspective (+/- fraction), range 0-0.001
    flipud=0.0,  # image flip up-down (probability)
    fliplr=0.5,  # image flip left-right (probability)
    mosaic=1.0,  # image mosaic (probability)
    mixup=0.0,  # image mixup (probability)
    copy_paste=0.0,  # segment copy-paste (probability)
)
