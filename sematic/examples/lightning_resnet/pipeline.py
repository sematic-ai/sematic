# Standard Library
import logging
from dataclasses import dataclass

# Third-party
import ray

# Sematic
import sematic
from sematic import context
from sematic.ee.ray import RayCluster, SimpleRayCluster
from sematic.examples.lightning_resnet.checkpointing import (
    Checkpoint,
    SematicCheckpointIO,
)
from sematic.examples.lightning_resnet.train_eval import (
    DataConfig,
    EvaluationConfig,
    EvaluationResults,
    TrainingConfig,
    evaluate_classifier,
    train_classifier,
)


@dataclass
class PipelineResults:
    """Data structure for holding results from training and evaluation"""

    final_checkpoint: Checkpoint
    evaluation_results: EvaluationResults


@sematic.func(inline=False)
def train(config: TrainingConfig, data_config: DataConfig) -> Checkpoint:
    """# Perform distributed training of a ResNet model.

    The model will be based on the
    [ResNet](https://pytorch.org/vision/stable/models/resnet.html?highlight=resnet)
    variant in Torchvision.

    It will be trainined using distributed training via [Ray](https://ray.io)

    ## Inputs
    - **config**: Configuration with compute and model parameters for training
    - **data_config**: Configuration for training data and data loading

    ## Output
    The best checkpoint produced during training
    """
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
    """# Evaluate a model checkpoint for a ResNet model.

    ## Inputs
    - **checkpoint**: A checkpoint for a trained model
    - **config**: Configuration for compute for evaluation
    - **data_config**: Configuration for the data to be used during evaluation

    ## Output
    Summary of some statistics resulting from the evaluation.
    """
    cluster_config = SimpleRayCluster(
        n_nodes=config.n_workers, node_config=config.worker
    )
    checkpointer = SematicCheckpointIO(s3_location=checkpoint.prefix)

    # we want the driver for the eval to run on the
    # small ray cluster we're creating.
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
    final_checkpoint: Checkpoint,
    evaluation_results: EvaluationResults,
) -> PipelineResults:
    """# Combine the results into a single data structure.

    This is necessary due to the fact that the results from training
    and evaluation are
    ["futures"](https://docs.sematic.dev/diving-deeper/future-algebra).
    """
    return PipelineResults(
        final_checkpoint=final_checkpoint,
        evaluation_results=evaluation_results,
    )


@sematic.func(inline=True)
def pipeline(
    train_config: TrainingConfig, data_config: DataConfig, eval_config: EvaluationConfig
) -> PipelineResults:
    """# Do distributed training & evaluation on a ResNet model

    The dataset the training will be performed on is
    [CIFAR10](https://www.cs.toronto.edu/~kriz/cifar.html)

    Distributed training will be performed using Sematic's
    [Ray integration](https://docs.sematic.dev/integrations/ray).

    Evaluation will also be distributed, though it will use its own
    (smaller) Ray cluster.

    ## Inputs
    - **train_config**: configuration for how training will be performed
    - **data_config**: configuration of the data & data loading that will be used
      for training and eval
    - **eval_config**: configuration for how the evaluation will be performed

    ## Output
    A summary of training performance, a link to the best checkpoint produced
    during training, and metrics about the evaluation of the model from that
    checkpoint.
    """
    model_checkpoint = train(train_config, data_config)
    evaluation_results = evaluate(model_checkpoint, eval_config, data_config)
    return bundle_results(model_checkpoint, evaluation_results)
