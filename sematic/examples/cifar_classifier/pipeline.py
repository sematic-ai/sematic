# Standard Library
from dataclasses import dataclass

# Third-party
from ray.train.torch.torch_checkpoint import TorchCheckpoint

# Sematic
import sematic
from sematic.ee.ray import RayCluster, SimpleRayCluster
from sematic.examples.cifar_classifier.train_eval import (
    EvaluationConfig,
    EvaluationResults,
    TrainingConfig,
    evaluate_classifier,
    train_classifier,
)


@dataclass
class PipelineResults:
    final_checkpoint: TorchCheckpoint
    evaluation_results: EvaluationResults


@sematic.func(inline=False)
def train(config: TrainingConfig) -> TorchCheckpoint:
    cluster_config = SimpleRayCluster(
        n_nodes=config.n_workers, node_config=config.worker
    )
    with RayCluster(config=cluster_config):
        return train_classifier(config)


@sematic.func(inline=False)
def evaluate(
    checkpoint: TorchCheckpoint, config: EvaluationConfig
) -> EvaluationResults:
    cluster_config = SimpleRayCluster(
        n_nodes=config.n_workers, node_config=config.worker
    )
    with RayCluster(config=cluster_config):
        return evaluate_classifier(checkpoint, config)


@sematic.func(inline=True)
def bundle_results(
    final_checkpoint: TorchCheckpoint, evaluation_results: EvaluationResults
) -> PipelineResults:
    return PipelineResults(
        final_checkpoint=final_checkpoint,
        evaluation_results=evaluation_results,
    )


@sematic.func(inline=True)
def pipeline(
    train_config: TrainingConfig, eval_config: EvaluationConfig
) -> PipelineResults:
    model_checkpoint = train(train_config)
    evaluation_results = evaluate(model_checkpoint, eval_config)
    return bundle_results(model_checkpoint, evaluation_results)
