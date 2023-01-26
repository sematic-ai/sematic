# Standard Library
import argparse

# Sematic
from sematic import LocalResolver, SilentResolver
from sematic.client import get_artifact_value

# YOLOv5
from sematic.examples.yolov5.configs.dataset import COCO128
from sematic.examples.yolov5.configs.evaluation import EvaluationConfig
from sematic.examples.yolov5.configs.hyperparameters import SCRATCH_LOW
from sematic.examples.yolov5.configs.model import YOLOV5L
from sematic.examples.yolov5.pipeline import (
    PipelineConfig,
    TrainingConfig,
    make_matplotlib_plot,
    pipeline,
)

CONFIG = PipelineConfig(
    device="",
    model_config=YOLOV5L,
    hyperparameters=SCRATCH_LOW,
    dataset_config=COCO128,
    training_config=TrainingConfig(),
    evaluation_config=EvaluationConfig(),
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("YOLO example")
    parser.add_argument("--silent", action="store_true", default=False)
    parser.add_argument("--model-id", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--cache-namespace", type=str, default=None)

    args = parser.parse_args()

    resolver = (
        SilentResolver()
        if args.silent
        else LocalResolver(cache_namespace=args.cache_namespace)
    )

    CONFIG.training_config.epochs = args.epochs

    model = None
    if args.model_id:
        model = get_artifact_value(args.model_id)

    pipeline(config=CONFIG, model=model).resolve(resolver)
