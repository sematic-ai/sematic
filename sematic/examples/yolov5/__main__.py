# Sematic
from sematic import SilentResolver

# YOLOv5
from sematic.examples.yolov5.configs.dataset import COCO128
from sematic.examples.yolov5.configs.hyperparameters import SCRATCH_LOW
from sematic.examples.yolov5.configs.model import YOLOV5L
from sematic.examples.yolov5.pipeline import PipelineConfig, TrainingConfig, pipeline

CONFIG = PipelineConfig(
    device="",
    model_config=YOLOV5L,
    hyperparameters=SCRATCH_LOW,
    dataset_config=COCO128,
    training_config=TrainingConfig(),
)


if __name__ == "__main__":
    pipeline(CONFIG).resolve(SilentResolver())
