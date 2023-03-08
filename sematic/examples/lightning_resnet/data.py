# Third-party
import pytorch_lightning as pl
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, random_split


class CifarDataModule(pl.LightningDataModule):
    """PyTorch Lightning DataModule for loading train/eval/test data.

    See:
    https://pytorch-lightning.readthedocs.io/en/stable/data/datamodule.html#why-do-i-need-a-datamodule
    """

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
