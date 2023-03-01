# This code is based on the example at:
# https://docs.ray.io/en/latest/ray-air/examples/torch_image_example.html
# Standard Library
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

# Third-party
import numpy as np
import ray
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from PIL.Image import Image
from plotly.graph_objs import Figure, Heatmap
from ray import train
from ray.air import RunConfig, session
from ray.air.config import ScalingConfig
from ray.data.preprocessors import TorchVisionPreprocessor
from ray.train.batch_predictor import BatchPredictor
from ray.train.torch import TorchCheckpoint, TorchPredictor, TorchTrainer
from ray.tune import SyncConfig

# Sematic
from sematic import context
from sematic.ee.ray import RayNodeConfig


def patched_set_state(self, state):
    if state.get("_data_dict", None) is not None:
        state = state.copy()
        state["_data_dict"] = self._decode_data_dict(state["_data_dict"])
    super(TorchCheckpoint, self).__setstate__(state)


TorchCheckpoint.__setstate__ = patched_set_state


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1)  # flatten all dimensions except batch
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


@dataclass
class EvaluationResults:
    accuracy: float
    n_correct: int
    n_samples: int
    confusion_matrix_plot: Figure


@dataclass
class TrainLoopConfig:
    batch_size: int
    n_epochs: int


@dataclass
class TrainingConfig:
    worker: RayNodeConfig
    n_workers: int
    checkpoint_dir: str
    loop_config: TrainLoopConfig


@dataclass
class EvaluationConfig:
    worker: RayNodeConfig
    n_workers: int


def load_dataset(is_train: bool) -> Tuple[ray.data.Dataset, List[str]]:
    dataset = torchvision.datasets.CIFAR10("data", download=True, train=is_train)
    classes = dataset.classes
    dataset: ray.data.Dataset = ray.data.from_torch(dataset)
    dataset = dataset.map_batches(convert_batch_to_numpy).fully_executed()

    return dataset, classes


def train_classifier(config: TrainingConfig) -> TorchCheckpoint:
    use_gpu = config.worker.gpu_count > 0
    if use_gpu:
        if ray.get(validate_gpus.remote()):
            print("Torch appears to be able to use GPUs on Ray")
        else:
            raise RuntimeError("GPUs could not be used by torch on Ray Cluster")

    train_dataset, _ = load_dataset(is_train=True)
    transform = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    )
    preprocessor = TorchVisionPreprocessor(columns=["image"], transform=transform)
    trainer = TorchTrainer(
        train_loop_per_worker=train_loop_per_worker,
        train_loop_config=asdict(config.loop_config),
        datasets={"train": train_dataset},
        scaling_config=ScalingConfig(num_workers=config.n_workers, use_gpu=use_gpu),
        run_config=RunConfig(
            sync_config=SyncConfig(
                upload_dir=f"{config.checkpoint_dir}/{context().run_id}",
            ),
        ),
        preprocessor=preprocessor,
    )
    result = trainer.fit()
    latest_checkpoint = result.checkpoint
    if latest_checkpoint is None:
        raise ValueError("No checkpoint produced from model")

    return latest_checkpoint


@ray.remote(num_gpus=1)
def validate_gpus():
    cuda_available = torch.cuda.is_available()
    return cuda_available


def evaluate_classifier(
    checkpoint: TorchCheckpoint, config: EvaluationConfig
) -> EvaluationResults:
    test_dataset, classes_list = load_dataset(is_train=False)
    batch_predictor = BatchPredictor.from_checkpoint(
        checkpoint=checkpoint,
        predictor_cls=TorchPredictor,
        model=Net(),
    )

    outputs: ray.data.Dataset = batch_predictor.predict(
        data=test_dataset,
        dtype=torch.float,
        feature_columns=["image"],
        keep_columns=["label"],
        # We will use GPU if available.
        num_gpus_per_worker=config.worker.gpu_count,
    )

    predictions = outputs.map_batches(convert_logits_to_classes)
    scores = predictions.map_batches(calculate_prediction_scores)
    confusion_matrix_data_frame = to_confusion_matrix_data_frame(
        predictions.map_batches(add_confusion_key)
        .groupby("confusion_key")
        .count()
        .to_pandas()
    )
    n_correct = scores.sum(on="correct")
    n_samples = scores.count()
    accuracy = n_correct / n_samples
    plot = create_confusion_matrix_plot(confusion_matrix_data_frame, classes_list)

    return EvaluationResults(
        accuracy=accuracy,
        n_correct=n_correct,
        n_samples=n_samples,
        confusion_matrix_plot=plot,
    )


def create_confusion_matrix_plot(confusion_matrix_data_frame, classes_list):
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


def convert_batch_to_numpy(batch: Tuple[Image, int]) -> Dict[str, np.ndarray]:
    images = np.stack([np.array(image) for image, _ in batch])
    labels = np.array([label for _, label in batch])
    return {"image": images, "label": labels}


def add_confusion_key(df):
    df["confusion_key"] = [
        f"{pred} : {label}" for pred, label in zip(df["prediction"], df["label"])
    ]
    return df


def to_confusion_matrix_data_frame(df):
    df["prediction"] = df["confusion_key"].map(
        lambda key: int(key.split(":")[0].strip())
    )
    df["label"] = df["confusion_key"].map(lambda key: int(key.split(":")[1].strip()))
    df = df.reset_index()
    del df["confusion_key"]
    df = df.rename(columns={"count()": "count"})
    return df.pivot(index="prediction", columns="label", values="count").fillna(0)


def calculate_prediction_scores(df):
    df["correct"] = df["prediction"] == df["label"]
    return df


def convert_logits_to_classes(df):
    best_class = df["predictions"].map(lambda x: x.argmax())
    df["prediction"] = best_class
    return df[["prediction", "label"]]


def train_loop_per_worker(config):
    model = train.torch.prepare_model(Net())

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

    train_dataset_shard = session.get_dataset_shard("train")
    n_epochs = config["n_epochs"]
    for epoch in range(n_epochs):
        running_loss = 0.0
        train_dataset_batches = train_dataset_shard.iter_torch_batches(
            batch_size=config["batch_size"], device=train.torch.get_device()
        )
        print(f"Training epoch {epoch + 1} of {n_epochs}")
        for i, batch in enumerate(train_dataset_batches):
            # get the inputs and labels
            inputs, labels = batch["image"], batch["label"]

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            # print statistics
            running_loss += loss.item()
            if i % 2000 == 1999:  # print every 2000 mini-batches
                print(f"[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}")
                running_loss = 0.0
                break

        metrics = dict(running_loss=running_loss)
        checkpoint = TorchCheckpoint.from_state_dict(model.state_dict())
        session.report(metrics, checkpoint=checkpoint)
