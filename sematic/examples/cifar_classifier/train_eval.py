# This code is based on the example at:
# https://docs.ray.io/en/latest/ray-air/examples/torch_image_example.html
# Standard Library
from dataclasses import asdict, dataclass
from io import BytesIO
from typing import Any, Dict, List, Tuple

# Third-party
import numpy as np
import pandas as pd
import ray
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from PIL import Image
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
from sematic.types.types.aws.s3 import S3Location
from sematic.types.types.image import Image as SematicImage


@dataclass
class ClassifiedImage:
    image: SematicImage
    predicted_class: str
    labeled_class: str


@dataclass
class EvaluationResults:
    accuracy: float
    n_correct: int
    n_samples: int
    confusion_matrix_plot: Figure
    sample_misclassifications: List[ClassifiedImage]


@dataclass
class TrainLoopConfig:
    batch_size: int
    n_epochs: int
    lr: float = 0.001
    momentum: float = 0.9


@dataclass
class TrainingConfig:
    worker: RayNodeConfig
    n_workers: int
    checkpoint_dir: S3Location
    loop_config: TrainLoopConfig


@dataclass
class EvaluationConfig:
    worker: RayNodeConfig
    n_workers: int
    n_sample_misclassifications: int


class Net(nn.Module):
    """A basic model to illustrate an image recognition task."""

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


def load_dataset(is_train: bool) -> Tuple[ray.data.Dataset, List[str]]:
    """Load (and fully materialize) the CIFAR10 dataset for training/evaluation"""
    dataset = torchvision.datasets.CIFAR10("data", download=True, train=is_train)
    classes = dataset.classes
    dataset: ray.data.Dataset = ray.data.from_torch(dataset)
    dataset = dataset.map_batches(convert_batch_to_numpy).fully_executed()

    return dataset, classes


def train_classifier(config: TrainingConfig) -> TorchCheckpoint:
    """Perform distributed training of the classifier model"""
    use_gpu = config.worker.gpu_count > 0
    if use_gpu:
        if ray.get(validate_gpus.remote()):
            print("Torch appears to be able to use GPUs on Ray")
        else:
            raise RuntimeError("GPUs could not be used by torch on Ray Cluster")

    train_dataset, _ = load_dataset(is_train=True)

    # Normalize the input image tensors. Preprocessing will take place on
    # ray workers.
    transform = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    )
    preprocessor = TorchVisionPreprocessor(columns=["image"], transform=transform)

    # initialize and execute the model trainer. Training will take
    # place distributedly on ray workers.
    trainer = TorchTrainer(
        train_loop_per_worker=train_loop_per_worker,
        train_loop_config=asdict(config.loop_config),
        datasets={"train": train_dataset},
        scaling_config=ScalingConfig(num_workers=config.n_workers, use_gpu=use_gpu),
        run_config=RunConfig(
            sync_config=SyncConfig(
                upload_dir=f"{config.checkpoint_dir.to_uri()}/{context().run_id}",
            ),
        ),
        preprocessor=preprocessor,
    )
    result = trainer.fit()

    latest_checkpoint = result.checkpoint
    if latest_checkpoint is None:
        raise ValueError("No checkpoint produced from model")

    # the to_dict/from_dict keeps full checkpoint as Sematic artifact
    return TorchCheckpoint.from_dict(latest_checkpoint.to_dict())


@ray.remote(num_gpus=1)
def validate_gpus() -> bool:
    """Helps confirm that GPUs can be used, and fail-fast if not."""
    cuda_available = torch.cuda.is_available()
    return cuda_available


def evaluate_classifier(
    checkpoint: TorchCheckpoint, config: EvaluationConfig
) -> EvaluationResults:
    """Perform evaluation on a model represented by the given checkpoint"""
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
        keep_columns=["label", "original_image", "image"],
        # We will use GPU if available.
        num_gpus_per_worker=config.worker.gpu_count,
    )

    predictions = outputs.map_batches(convert_logits_to_classes)
    scores = predictions.map_batches(calculate_prediction_scores)
    misclassified = predictions.filter(filter_to_misclassified)
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

    missclassified_images_df = misclassified.limit(
        config.n_sample_misclassifications
    ).to_pandas()
    sample_misclassifications = get_sample_misclassifications_from_df(
        missclassified_images_df, classes_list
    )

    return EvaluationResults(
        accuracy=accuracy,
        n_correct=n_correct,
        n_samples=n_samples,
        confusion_matrix_plot=plot,
        sample_misclassifications=sample_misclassifications,
    )


def filter_to_misclassified(prediction_row):
    return prediction_row["prediction"] != prediction_row["label"]


def get_sample_misclassifications_from_df(
    missclassified_images_df: pd.DataFrame, classes_list: List[str]
) -> List[ClassifiedImage]:
    def _array_to_jpg(original_image_array):
        image = Image.fromarray(original_image_array.to_numpy())
        byte_buffer = BytesIO()
        image.save(byte_buffer, format="jpeg")
        return SematicImage(bytes=byte_buffer.getvalue())

    return [
        ClassifiedImage(
            image=_array_to_jpg(row["original_image"]),
            predicted_class=classes_list[row["prediction"]],
            labeled_class=classes_list[row["label"]],
        )
        for _, row in missclassified_images_df.iterrows()
    ]


def create_confusion_matrix_plot(
    confusion_matrix_data_frame: pd.DataFrame, classes_list: List[str]
) -> Figure:
    """Plot a confusion matrix as a Plotly image

    Parameters
    ----------
    confusion_matrix_data_frame:
        Data frame structured as a pivot table where the row index is predicted
        class, the column index is labeled class, and the values are the number
        of occurrences of that prediction/label pair.
    classes_list:
        A list of the human-readable classes the prediction is being run for,
        ordered such that element 0 is the name for the class that a prediction
        of 0 corresponds to, element 1 is the name for class 1, etc..

    Returns
    -------
    A plotly image of a confusion matrix.
    """
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


def convert_batch_to_numpy(batch: List[Tuple[Image.Image, int]]) -> Dict[str, np.ndarray]:
    """Convert a batch PIL images and their labels to Ray's numpy batch format.

    Parameters
    ----------
    batch:
        A batch of tuples where each tuple holds a PIL Image and its labeled class

    Returns
    -------
    A dict where the keys are "image", "label", and "original_image". The value
    for "image" is an array of images with each image as a 3d numpy array
    (x/y/channel). The value for "labels" is an array of predicted classes
    for each of the images. The value of "original_image" is the PIL.Image.Image
    representation of the image.
    """

    def _pil_to_jpg_bytes(pil_image):
        byte_buffer = BytesIO()
        pil_image.save(byte_buffer, format="jpeg")
        return np.array(pil_image)

    images = np.stack([np.array(image) for image, _ in batch])
    labels = np.array([label for _, label in batch])
    original_images = np.stack([np.array(image) for image, _ in batch])
    return {"image": images, "label": labels, "original_image": original_images}


def add_confusion_key(df: pd.DataFrame) -> pd.DataFrame:
    """Add a column "confusion_key" to a dataframe with prediction & label keys.

    The confusion_key column will hold strings of the form "<prediction> : <label>"
    """
    df["confusion_key"] = [
        f"{pred} : {label}" for pred, label in zip(df["prediction"], df["label"])
    ]
    return df


def to_confusion_matrix_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Given a data frame with column "confusion_key" to a pivot table confusion matrix.

    The confusion_key column should be structured as strings of the form
    "<prediction> : <label>"

    Returns
    -------
    A data frame structured as a pivot table where rows are indexed by the predicted
    class, columns are indexed by the labeled class, and the values are the number
    of times the given prediction/label pair occurred.
    """
    df["prediction"] = df["confusion_key"].map(lambda key: int(key.split(":")[0].strip()))
    df["label"] = df["confusion_key"].map(lambda key: int(key.split(":")[1].strip()))
    df = df.reset_index()
    del df["confusion_key"]
    df = df.rename(columns={"count()": "count"})
    return df.pivot(index="prediction", columns="label", values="count").fillna(0)


def calculate_prediction_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Add a "correct" column to a data frame indicating if the prediction was correct.

    Input data frame should have "prediction" and "label" columns.
    """
    df["correct"] = df["prediction"] == df["label"]
    del df["original_image"]
    del df["image"]
    return df


def convert_logits_to_classes(df: pd.DataFrame) -> pd.DataFrame:
    """Convert the "prediction" column of the data frame from logits to classes."""
    best_class = df["predictions"].map(lambda x: x.argmax())
    df["prediction"] = best_class
    return df[["prediction", "label", "original_image", "image"]]


def train_loop_per_worker(config: Dict[str, Any]) -> None:
    """This is the training loop that each train worker will iterate over.

    A checkpoint will be registered by the train workers each epoch
    """
    model = train.torch.prepare_model(Net())

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(
        model.parameters(), lr=config["lr"], momentum=config["momentum"]
    )

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
