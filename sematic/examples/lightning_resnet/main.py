# Standard Library
import argparse
import logging
from dataclasses import replace

# Sematic
import sematic
from sematic.ee.ray import RayNodeConfig
from sematic.examples.lightning_resnet.pipeline import pipeline
from sematic.examples.lightning_resnet.train_eval import (
    DataConfig,
    EvaluationConfig,
    TrainingConfig,
    TrainLoopConfig,
)
from sematic.types.types.aws.s3 import S3Location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHECKPOINT_LOCATION = S3Location.from_uri("s3://sematic-dev/lightning-resnet")

LOCAL_DATA_CONFIG = DataConfig(
    batch_size=2,
    train_fraction=0.9,
    n_workers=4,
)

REMOTE_DATA_CONFIG = replace(LOCAL_DATA_CONFIG, batch_size=256)

LOCAL_TRAINING_CONFIG = TrainingConfig(
    n_workers=2,
    worker=RayNodeConfig(
        cpu=2,
        memory_gb=8,
        gpu_count=0,
    ),
    loop_config=TrainLoopConfig(
        n_epochs=1,
        max_steps=250,
    ),
    checkpoint_location=CHECKPOINT_LOCATION,
)

REMOTE_TRAINING_CONFIG = TrainingConfig(
    n_workers=4,
    worker=RayNodeConfig(
        cpu=3,
        memory_gb=10,
        gpu_count=1,
    ),
    loop_config=TrainLoopConfig(
        n_epochs=80,
        max_steps=-1,
    ),
    checkpoint_location=CHECKPOINT_LOCATION,
)

LOCAL_EVAL_CONFIG = EvaluationConfig(
    n_workers=2,
    worker=RayNodeConfig(
        cpu=2,
        memory_gb=8,
        gpu_count=0,
    ),
)

REMOTE_EVAL_CONFIG = EvaluationConfig(
    n_workers=2,
    worker=RayNodeConfig(
        cpu=3,
        memory_gb=10,
        gpu_count=1,
    ),
)


def main():
    parser = argparse.ArgumentParser("Lightning CIFAR Classifier Example")
    parser.add_argument("--cloud", default=False, action="store_true")

    args = parser.parse_args()

    logger.info("Starting CIFAR Classifier example...")

    if args.cloud:
        resolver = sematic.CloudResolver()
        train_config = REMOTE_TRAINING_CONFIG
        eval_config = REMOTE_EVAL_CONFIG
        data_config = REMOTE_DATA_CONFIG
    else:
        resolver = sematic.LocalResolver()
        train_config = LOCAL_TRAINING_CONFIG
        eval_config = LOCAL_EVAL_CONFIG
        data_config = LOCAL_DATA_CONFIG

    future = pipeline(train_config, data_config, eval_config).set(
        name="Distributed Training Resnet Example"
    )

    print(future.resolve(resolver))


if __name__ == "__main__":
    main()
