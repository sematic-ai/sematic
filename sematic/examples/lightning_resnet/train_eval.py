# This example is adapted from one at:
# https://pytorch-lightning.readthedocs.io/en/stable/notebooks/lightning_examples/cifar10-baseline.html
# It is available under the license CC BY-SA:
# https://creativecommons.org/licenses/by-sa/2.0/

# Standard Library
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party
import pandas as pd
import ray
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchmetrics
import torchvision
from plotly.graph_objs import Figure, Heatmap
from pytorch_lightning import LightningModule, Trainer, seed_everything
from pytorch_lightning.callbacks import LearningRateMonitor
from pytorch_lightning.callbacks.progress import TQDMProgressBar
from pytorch_lightning.loggers import CSVLogger
from ray_lightning import RayStrategy
from torch.optim.lr_scheduler import OneCycleLR

# Sematic
from sematic.ee.ray import RayNodeConfig
from sematic.examples.lightning_resnet.checkpointing import (
    Checkpoint,
    SematicCheckpointIO,
)
from sematic.examples.lightning_resnet.data import CifarDataModule
from sematic.types.types.aws.s3 import S3Location


class LitResnet(LightningModule):
    """Simple wrapper around Torchvision ResNet.

    https://pytorch.org/vision/stable/models/resnet.html?highlight=resnet
    """

    def __init__(
        self,
        batch_size: int,
        num_classes: int,
        num_samples_per_epoch: int,
        lr: float = 0,
        momentum: float = 0,
        weight_decay: float = 0,
    ):
        super().__init__()
        self.batch_size = batch_size
        self.num_samples_per_epoch = num_samples_per_epoch
        self.save_hyperparameters()
        self.model = create_model(num_classes)
        self.accuracy = torchmetrics.Accuracy(task="multiclass", num_classes=num_classes)
        self.num_classes = num_classes

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.model(x)
        return F.log_softmax(out, dim=1)

    def training_step(self, batch: torch.Tensor, batch_idx: int) -> torch.Tensor:
        x, y = batch
        logits = self(x)
        loss = F.nll_loss(logits, y)
        self.log("train_loss", loss)
        return loss

    def evaluate(self, batch: torch.Tensor, stage: Optional[str] = None):
        x, y = batch
        logits = self(x)
        loss = F.nll_loss(logits, y)
        preds = torch.argmax(logits, dim=1)
        acc = self.accuracy(preds, y)

        if stage:
            self.log(f"{stage}_loss", loss, prog_bar=True)
            self.log(f"{stage}_accuracy", acc, prog_bar=True)
            if stage in ("fit", "val"):
                # don't want to waste compute resources during training on these
                # more detailed metrics
                return
            self.log(
                f"{stage}_n_samples", float(len(preds)), reduce_fx="sum", sync_dist=True
            )
            count_by_confusion_key = Counter()
            for pred, label in zip(preds, y):
                count_by_confusion_key[
                    (int(pred.cpu().numpy()), int(label.cpu().numpy()))
                ] += 1
            for key, val in self._create_confusion_metrics(stage, count_by_confusion_key):
                self.log(key, val, reduce_fx="sum", sync_dist=True)

    def _create_confusion_metrics(
        self, stage: str, count_by_confusion_key: Dict[str, int]
    ) -> List[Tuple[str, float]]:
        metric_key_value_pairs = []
        for (pred, label), count in count_by_confusion_key.items():
            metric_key_value_pairs.append(
                (f"{stage}_{pred}_{label}_confusion", float(count))
            )
        return metric_key_value_pairs

    def _read_confusion_metrics(
        self, stage: str, metrics: List[Dict[str, float]]
    ) -> pd.DataFrame:
        confusion_dicts = [
            {
                "prediction": int(k.split("_")[1]),
                "label": int(k.split("_")[2]),
                "count": int(v),
            }
            for k, v in metrics[-1].items()
            if k.endswith("confusion") and k.startswith(stage)
        ]

        # Sometimes not all classes will show up in the predictions for small samples or
        # bad models. We want the dicts to contain at least one of each prediction class
        # so the table has every expected row.
        missing_predictions = set(range(self.num_classes)).difference(
            row["prediction"] for row in confusion_dicts
        )
        for missing_prediction in missing_predictions:
            # since this prediction didn't show up AT ALL, we know the count for
            # label 0 is 0.
            confusion_dicts.append(
                {"prediction": missing_prediction, "label": 0, "count": 0}
            )

        # Similar thing with missing labels: small evaluation data might not
        # have them all, but we want 0 example of each label so the table has
        # every expected column.
        missing_labels = set(range(self.num_classes)).difference(
            row["label"] for row in confusion_dicts
        )
        for missing_label in missing_labels:
            # we know this label didn't show up, so the count for prediction 0
            # is definitely 0.
            confusion_dicts.append({"prediction": 0, "label": missing_label, "count": 0})

        return (
            pd.DataFrame(confusion_dicts)
            .pivot(index="prediction", columns="label", values="count")
            .fillna(0)
        )

    def validation_step(self, batch: torch.Tensor, batch_idx: int) -> None:
        self.evaluate(batch, "val")

    def test_step(self, batch: torch.Tensor, batch_idx: int) -> None:
        self.evaluate(batch, "test")

    def configure_optimizers(self) -> Dict[str, Any]:
        optimizer = torch.optim.SGD(
            self.parameters(),
            lr=self.hparams.lr,
            momentum=self.hparams.momentum,
            weight_decay=self.hparams.weight_decay,
        )
        steps_per_epoch = self.num_samples_per_epoch // self.batch_size
        scheduler_dict = {
            "scheduler": OneCycleLR(
                optimizer,
                0.1,
                epochs=self.trainer.max_epochs,
                steps_per_epoch=steps_per_epoch,
            ),
            "interval": "step",
        }
        return {"optimizer": optimizer, "lr_scheduler": scheduler_dict}


@dataclass
class EvaluationResults:
    accuracy: float
    n_correct: int
    n_samples: int
    confusion_matrix_plot: Figure


@dataclass
class TrainLoopConfig:
    n_epochs: int
    max_steps: int
    learning_rate: float
    momentum: float
    weight_decay: float


@dataclass
class DataConfig:
    batch_size: int
    train_fraction: float = 0.1
    n_workers: int = 4


@dataclass
class TrainingConfig:
    worker: RayNodeConfig
    n_workers: int
    loop_config: TrainLoopConfig
    checkpoint_location: S3Location


@dataclass
class EvaluationConfig:
    worker: RayNodeConfig
    n_workers: int


def load_dataset(is_train: bool) -> torchvision.datasets.CIFAR10:
    dataset = torchvision.datasets.CIFAR10("data", download=True, train=is_train)
    return dataset


def train_classifier(
    config: TrainingConfig,
    data_config: DataConfig,
    strategy_compute_kwargs: Dict[str, Union[float, int, bool]],
    checkpointer: SematicCheckpointIO,
) -> Checkpoint:
    seed_everything(42)
    use_gpu = config.worker.gpu_count > 0
    if use_gpu:
        if ray.get(validate_gpus.remote()):
            print("Torch appears to be able to use GPUs on Ray")
        else:
            raise RuntimeError("GPUs could not be used by torch on Ray Cluster")

    cifar_dm = CifarDataModule(
        batch_size=data_config.batch_size,
        train_fraction=data_config.train_fraction,
        n_workers=data_config.n_workers,
    )
    cifar_dm.setup("fit")

    model = LitResnet(
        data_config.batch_size,
        num_classes=len(cifar_dm.classes),
        lr=config.loop_config.learning_rate,
        momentum=config.loop_config.momentum,
        weight_decay=config.loop_config.weight_decay,
        num_samples_per_epoch=cifar_dm.n_train,
    )

    strategy = RayStrategy(
        checkpoint_io=checkpointer,
        find_unused_parameters=False,
        **strategy_compute_kwargs,
    )
    trainer = Trainer(
        max_epochs=config.loop_config.n_epochs,
        devices=config.worker.gpu_count if config.worker.gpu_count > 0 else None,
        logger=CSVLogger(save_dir="logs/"),
        max_steps=config.loop_config.max_steps,
        callbacks=[
            LearningRateMonitor(logging_interval="step"),
            TQDMProgressBar(refresh_rate=10),
        ],
        strategy=strategy,
    )
    trainer.fit(model, datamodule=cifar_dm)

    return checkpointer.from_path(trainer.checkpoint_callback.best_model_path)


@ray.remote(num_gpus=1)
def validate_gpus() -> bool:
    cuda_available = torch.cuda.is_available()
    return cuda_available


def create_model(num_classes: int) -> torch.nn.Module:
    model = torchvision.models.resnet18(weights=None, num_classes=num_classes)
    model.conv1 = nn.Conv2d(
        3, 64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), bias=False
    )
    model.maxpool = nn.Identity()
    return model


def evaluate_classifier(
    checkpoint: Checkpoint,
    config: EvaluationConfig,
    data_config: DataConfig,
    strategy_compute_kwargs: Dict[str, Union[float, int, bool]],
    checkpointer: SematicCheckpointIO,
) -> EvaluationResults:
    cifar_dm = CifarDataModule(
        batch_size=data_config.batch_size,
        train_fraction=data_config.train_fraction,
        n_workers=data_config.n_workers,
    )
    cifar_dm.setup("test")

    strategy = RayStrategy(
        checkpoint_io=checkpointer,
        find_unused_parameters=False,
        **strategy_compute_kwargs,
    )
    trainer = Trainer(
        max_epochs=1,
        devices=config.worker.gpu_count if config.worker.gpu_count > 0 else None,
        logger=CSVLogger(save_dir="logs/"),
        strategy=strategy,
    )

    model = LitResnet(
        batch_size=data_config.batch_size,
        num_classes=len(cifar_dm.classes),
        num_samples_per_epoch=-1,
    )
    metrics = trainer.test(model=model, ckpt_path=checkpoint.path, datamodule=cifar_dm)

    confusion_matrix_data_frame = model._read_confusion_metrics("test", metrics)
    confusion_plot = plot_confusion(confusion_matrix_data_frame, cifar_dm.classes)
    return EvaluationResults(
        accuracy=metrics[-1]["test_accuracy"],
        n_correct=int(metrics[-1]["test_n_samples"] * metrics[-1]["test_accuracy"]),
        n_samples=metrics[-1]["test_n_samples"],
        confusion_matrix_plot=confusion_plot,
    )


def plot_confusion(
    confusion_matrix_data_frame: pd.DataFrame, classes_list: List[str]
) -> Figure:
    data = Heatmap(
        z=confusion_matrix_data_frame.T,
        text=confusion_matrix_data_frame.T,
        texttemplate="%{text}",
        x=confusion_matrix_data_frame.index.map(lambda i: classes_list[i]),
        y=confusion_matrix_data_frame.columns.map(lambda i: classes_list[i]),
    )
    layout = {
        "title": "Confusion Matrix",
        "xaxis": {"title": "Predicted class"},
        "yaxis": {"title": "Labeled class"},
    }
    return Figure(data=data, layout=layout)
