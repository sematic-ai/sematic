# Standard Library
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Union

# Third-party
import pandas as pd
import plotly.express as px
import pytorch_lightning as pl
import ray
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchmetrics
import torchvision
import torchvision.transforms as transforms
from plotly.graph_objs import Figure, Heatmap, Scatter
from pytorch_lightning import LightningModule, Trainer, seed_everything
from pytorch_lightning.callbacks import Callback, LearningRateMonitor
from pytorch_lightning.callbacks.progress import TQDMProgressBar
from pytorch_lightning.loggers import CSVLogger
from ray_lightning import RayStrategy
from torch.optim.lr_scheduler import OneCycleLR
from torch.utils.data import DataLoader, random_split

# Sematic
from sematic.ee.ray import RayNodeConfig
from sematic.examples.lightning_resnet.checkpointing import (
    Checkpoint,
    SematicCheckpointIO,
)
from sematic.types.types.aws.s3 import S3Location


class CifarDataModule(pl.LightningDataModule):
    def __init__(
        self,
        batch_size,
        train_fraction,
        n_workers,
        base_class=torchvision.datasets.CIFAR10,
    ):
        super().__init__()
        train_transform = torchvision.transforms.Compose(
            [
                torchvision.transforms.RandomCrop(32, padding=4),
                torchvision.transforms.RandomHorizontalFlip(),
                torchvision.transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ]
        )

        test_transform = torchvision.transforms.Compose(
            [
                torchvision.transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ]
        )
        self.batch_size = batch_size
        self.base_class = base_class
        self.train_transform = train_transform
        self.test_transform = test_transform
        self.train_fraction = train_fraction
        self.train = None
        self.eval = None
        self.test = None
        self.predict = None
        self.classes = None
        self.n_workers = n_workers
        self.n_train = None
        self.n_eval = None

    def setup(self, stage: str):
        # Assign train/val datasets for use in dataloaders
        if stage == "fit":
            full = self.base_class(
                "data", train=True, download=True, transform=self.train_transform
            )
            self.classes = full.classes
            total = len(full.data)
            self.n_train = int(self.train_fraction * total)
            self.n_eval = total - self.n_train
            self.train, self.eval = random_split(full, [self.n_train, self.n_eval])
        elif stage == "test":
            self.test = self.base_class(
                "data", train=False, download=True, transform=self.test_transform
            )
            self.classes = self.test.classes
        elif stage == "predict":
            self.predict = self.base_class(
                "data", train=False, download=True, transform=self.test_transform
            )
            self.classes = self.predict.classes
        else:
            raise ValueError(f"Unsupported stage '{stage}'")

    def train_dataloader(self):
        return DataLoader(
            self.train, num_workers=self.n_workers, batch_size=self.batch_size
        )

    def val_dataloader(self):  # trainer._data_connector._val_dataloader_source
        return DataLoader(
            self.eval, num_workers=self.n_workers, batch_size=self.batch_size
        )

    def test_dataloader(self):
        return DataLoader(
            self.test, num_workers=self.n_workers, batch_size=self.batch_size
        )

    def predict_dataloader(self):
        return DataLoader(
            self.predict, num_workers=self.n_workers, batch_size=self.batch_size
        )

    def teardown(self, stage: str):
        pass
