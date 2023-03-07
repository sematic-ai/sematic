# Standard Library
import argparse
import logging

# Sematic
import sematic
from sematic.ee.ray import RayNodeConfig
from sematic.examples.cifar_classifier.pipeline import pipeline
from sematic.examples.cifar_classifier.train_eval import (
    EvaluationConfig,
    TrainingConfig,
    TrainLoopConfig,
)
from sematic.types.types.aws.s3 import S3Location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCAL_TRAINING_CONFIG = TrainingConfig(
    n_workers=1,
    worker=RayNodeConfig(
        cpu=2,
        memory_gb=8,
        gpu_count=0,
    ),
    checkpoint_dir=S3Location.from_uri("s3://sematic-dev/ray-demo"),
    loop_config=TrainLoopConfig(
        batch_size=2,
        n_epochs=1,
    ),
)

REMOTE_TRAINING_CONFIG = TrainingConfig(
    n_workers=4,
    worker=RayNodeConfig(
        cpu=3,
        memory_gb=10,
        gpu_count=1,
    ),
    checkpoint_dir=S3Location.from_uri("s3://sematic-dev/ray-demo"),
    loop_config=TrainLoopConfig(
        batch_size=4,
        n_epochs=5,
    ),
)

LOCAL_EVAL_CONFIG = EvaluationConfig(
    n_workers=1,
    worker=RayNodeConfig(
        cpu=2,
        memory_gb=8,
        gpu_count=0,
    ),
)

REMOTE_EVAL_CONFIG = EvaluationConfig(
    n_workers=1,
    worker=RayNodeConfig(
        cpu=3,
        memory_gb=10,
        gpu_count=1,
    ),
)


def main():
    parser = argparse.ArgumentParser("CIFAR Classifier Example")
    parser.add_argument("--cloud", default=False, action="store_true")

    args = parser.parse_args()

    logger.info("Starting CIFAR Classifier example...")

    if args.cloud:
        resolver = sematic.CloudResolver()
        train_config = REMOTE_TRAINING_CONFIG
        eval_config = REMOTE_EVAL_CONFIG
    else:
        resolver = sematic.LocalResolver()
        train_config = LOCAL_TRAINING_CONFIG
        eval_config = LOCAL_EVAL_CONFIG

    future = pipeline(train_config, eval_config).set(name="CIFAR Classifier Example")

    print(future.resolve(resolver))


if __name__ == "__main__":
    main()
