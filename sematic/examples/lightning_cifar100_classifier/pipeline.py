# Standard Library
import logging
from dataclasses import dataclass

# Third-party
import ray

# Sematic
import sematic
from sematic import context
from sematic.ee.ray import RayCluster, SimpleRayCluster
from sematic.examples.lightning_cifar100_classifier.checkpointing import (
    Checkpoint,
    SematicCheckpointIO,
)
from sematic.examples.lightning_cifar100_classifier.train_eval import (
    DataConfig,
    EvaluationConfig,
    EvaluationResults,
    TrainingConfig,
    evaluate_classifier,
    train_classifier,
)


@dataclass
class PipelineResults:
    final_checkpoint: Checkpoint
    evaluation_results: EvaluationResults


@sematic.func(inline=False)
def train(config: TrainingConfig, data_config: DataConfig) -> Checkpoint:
    cluster_config = SimpleRayCluster(
        n_nodes=config.n_workers, node_config=config.worker
    )

    # You can also use the built-in pytorch lightning checkpointing
    # with s3 if you are willing to install some extra dependencies
    checkpointer = SematicCheckpointIO(
        s3_location=config.checkpoint_location / context().run_id
    )

    # we want the driver for the training to run on the
    # small ray cluster we're creating.
    @ray.remote(num_cpus=config.worker.cpu, num_gpus=config.worker.gpu_count)
    def call_train_classifier_from_ray():
        logging.basicConfig(level=logging.INFO)
        strategy_compute_kwargs = dict(
            # -1 because 1 worker is being used to drive the training.
            num_workers=config.n_workers - 1,
            num_cpus_per_worker=config.worker.cpu,
            use_gpu=config.worker.gpu_count > 0,
        )
        return train_classifier(
            config, data_config, strategy_compute_kwargs, checkpointer
        )

    with RayCluster(config=cluster_config):
        return ray.get(call_train_classifier_from_ray.remote())


@sematic.func(inline=False)
def evaluate(
    checkpoint: Checkpoint, config: EvaluationConfig, data_config: DataConfig
) -> EvaluationResults:
    cluster_config = SimpleRayCluster(
        n_nodes=config.n_workers, node_config=config.worker
    )
    checkpointer = SematicCheckpointIO(s3_location=checkpoint.prefix)

    @ray.remote(num_gpus=config.worker.gpu_count)
    def call_evaluate_classifier_from_ray():
        logging.basicConfig(level=logging.INFO)
        strategy_compute_kwargs = dict(
            num_workers=config.n_workers - 1,
            num_cpus_per_worker=config.worker.cpu,
            use_gpu=config.worker.gpu_count > 0,
        )
        return evaluate_classifier(
            checkpoint, config, data_config, strategy_compute_kwargs, checkpointer
        )

    with RayCluster(config=cluster_config):
        return ray.get(call_evaluate_classifier_from_ray.remote())


@sematic.func(inline=True)
def bundle_results(
    final_checkpoint: Checkpoint, evaluation_results: EvaluationResults
) -> PipelineResults:
    return PipelineResults(
        final_checkpoint=final_checkpoint,
        evaluation_results=evaluation_results,
    )


@sematic.func(inline=True)
def pipeline(
    train_config: TrainingConfig, data_config: DataConfig, eval_config: EvaluationConfig
) -> PipelineResults:
    model_checkpoint = train(train_config, data_config)
    evaluation_results = evaluate(model_checkpoint, eval_config, data_config)
    return bundle_results(model_checkpoint, evaluation_results)
