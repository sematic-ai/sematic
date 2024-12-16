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


@sematic.func(standalone=True)
def train(config: TrainingConfig) -> TorchCheckpoint:
    """# Train an image classifier on the CIFAR10 dataset

    ## Inputs
    - **config**: configuration for the compute and hyperparameters to be
    used for training

    ## Returns
    The last checkpoint produced during training
    """
    cluster_config = SimpleRayCluster(n_nodes=config.n_workers, node_config=config.worker)
    with RayCluster(config=cluster_config):
        return train_classifier(config)


@sematic.func(standalone=True)
def evaluate(checkpoint: TorchCheckpoint, config: EvaluationConfig) -> EvaluationResults:
    """# Run evaluation data on an image classification model

    ## Inputs
    - **checkpoint**: The checkpoint from training containing the model parameters to
    be evaluated
    - **config**: The configuration for the compute to be used during evaluation

    ## Returns
    Some basic statistics on the evaluation, and a confusion matrix plot for the
    evaluation.
    """
    cluster_config = SimpleRayCluster(n_nodes=config.n_workers, node_config=config.worker)
    with RayCluster(config=cluster_config):
        return evaluate_classifier(checkpoint, config)


@sematic.func
def bundle_results(
    final_checkpoint: TorchCheckpoint, evaluation_results: EvaluationResults
) -> PipelineResults:
    """# Combine the results into a single data structure

    This is necessary due to the fact that the results from training
    and evaluation are
    ["futures"](https://docs.sematic.dev/diving-deeper/future-algebra).
    """
    return PipelineResults(
        final_checkpoint=final_checkpoint,
        evaluation_results=evaluation_results,
    )


@sematic.func
def pipeline(
    train_config: TrainingConfig, eval_config: EvaluationConfig
) -> PipelineResults:
    """# Perform distributed training followed by distributed evaluation

    The model being trained and evaluated is a simple pytorch image
    classifier for the [CIFAR10](https://www.cs.toronto.edu/~kriz/cifar.html)
    dataset.

    The distributed training will be done using [Ray](https://ray.io).
    Ray's [AIR](https://docs.ray.io/en/latest/ray-air/getting-started.html)
    APIs will be used to abstract away the training and handle checkpointing
    during training.

    ## Inputs
    - **train_config**: Configuration for the training of the model
    - **eval_config**: Configuration for the evaluation of the trained model

    ## Returns
    Summary information about the training, as well as summary stats from the
    evaluation.
    """
    model_checkpoint = train(train_config)
    evaluation_results = evaluate(model_checkpoint, eval_config)
    return bundle_results(model_checkpoint, evaluation_results)
