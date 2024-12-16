# Standard Library
import argparse
import logging
from dataclasses import replace

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

DEFAULT_CHECKPOINT_DIR = S3Location.from_uri("s3://sematic-examples/ray-cifar-example")

LOCAL_TRAINING_CONFIG = TrainingConfig(
    n_workers=1,
    worker=RayNodeConfig(
        cpu=2,
        memory_gb=8,
        gpu_count=0,
    ),
    checkpoint_dir=DEFAULT_CHECKPOINT_DIR,
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
    checkpoint_dir=DEFAULT_CHECKPOINT_DIR,
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
    n_sample_misclassifications=10,
)

REMOTE_EVAL_CONFIG = EvaluationConfig(
    n_workers=1,
    worker=RayNodeConfig(
        cpu=3,
        memory_gb=10,
        gpu_count=1,
    ),
    n_sample_misclassifications=10,
)


def main():
    parser = argparse.ArgumentParser("CIFAR Classifier Example")
    parser.add_argument(
        "--cloud",
        default=False,
        action="store_true",
        help="Whether to use CloudRunner (otherwise LocalRunner is used)",
    )
    parser.add_argument(
        "--checkpoint-dir",
        default=DEFAULT_CHECKPOINT_DIR,
        type=S3Location.from_uri,
        help="S3 URI to store checkpoints at.",
    )

    args = parser.parse_args()

    logger.info("Starting CIFAR Classifier example...")

    if args.cloud:
        runner = sematic.CloudRunner()
        train_config = REMOTE_TRAINING_CONFIG
        eval_config = REMOTE_EVAL_CONFIG
    else:
        runner = sematic.LocalRunner()
        train_config = LOCAL_TRAINING_CONFIG
        eval_config = LOCAL_EVAL_CONFIG

    train_config = replace(train_config, checkpoint_dir=args.checkpoint_dir)

    future = pipeline(train_config, eval_config).set(name="CIFAR Classifier Example")

    runner.run(future)


if __name__ == "__main__":
    main()
