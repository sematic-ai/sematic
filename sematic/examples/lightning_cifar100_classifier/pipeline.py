# Standard Library
from dataclasses import dataclass

import ray

# Sematic
import sematic
from sematic import context
from sematic.ee.ray import RayCluster, SimpleRayCluster
from sematic.examples.lightning_cifar100_classifier.train_eval import (
    EvaluationConfig,
    EvaluationResults,
    TrainingConfig,
    evaluate_classifier,
    train_classifier,
    DataConfig,
)
from sematic.examples.lightning_cifar100_classifier.checkpointing import SematicCheckpointIO, Checkpoint


@dataclass
class PipelineResults:
    final_checkpoint: Checkpoint
    evaluation_results: EvaluationResults


@sematic.func(inline=False)
def train(config: TrainingConfig, data_config: DataConfig) -> Checkpoint:
    cluster_config = SimpleRayCluster(
        n_nodes=config.n_workers, node_config=config.worker
    )
    checkpointer = SematicCheckpointIO(run_id=context().run_id)

    @ray.remote(num_cpus=config.worker.cpu, num_gpus=config.worker.gpu_count)
    def call_train_classifier_from_ray():
        strategy_compute_kwargs = dict(num_workers=config.n_workers - 1, num_cpus_per_worker=config.worker.cpu, use_gpu=config.worker.gpu_count > 0)
        return train_classifier(config, data_config, strategy_compute_kwargs, checkpointer)

    with RayCluster(config=cluster_config):        
        return ray.get(call_train_classifier_from_ray.remote())


@sematic.func(inline=False)
def evaluate(
    checkpoint: Checkpoint, config: EvaluationConfig, data_config: DataConfig
) -> EvaluationResults:
    cluster_config = SimpleRayCluster(
        n_nodes=config.n_workers, node_config=config.worker
    )
    checkpointer = SematicCheckpointIO(run_id=checkpoint.source_run_id)

    @ray.remote(num_gpus=config.worker.gpu_count)
    def call_evaluate_classifier_from_ray():
        strategy_compute_kwargs = dict(num_workers=config.n_workers - 1, num_cpus_per_worker=config.worker.cpu, use_gpu=config.worker.gpu_count > 0)
        return evaluate_classifier(checkpoint, config, data_config, strategy_compute_kwargs, checkpointer)
    
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