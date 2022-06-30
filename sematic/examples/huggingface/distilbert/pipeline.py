from dataclasses import dataclass
import sematic
import numpy as np
import os

from datasets import load_dataset, load_metric, DatasetDict, Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DistilBertForSequenceClassification,
)

os.environ["WANDB_DISABLED"] = "true"


@dataclass
class PipelineConfig:
    number_of_training_samples: int = 20
    number_of_test_samples: int = 20
    seed: int = 42


@sematic.func
def pipeline(
    training_args: TrainingArguments, config: PipelineConfig
) -> DistilBertForSequenceClassification:
    """
    This is a basic example of using [HuggingFace DistilBERT
    🤗](https://huggingface.co/docs/transformers/model_doc/distilbert) for
    sequence classification.

    In this case, we're using a dataset of [Yelp
    Reviews](https://huggingface.co/datasets/yelp_review_full) which classifies
    a sequence for a rating between 1-5 stars.
    """
    dataset = load_yelp_dataset()

    tokenized_datasets = tokenize_dataset(dataset)

    small_train_dataset = train_and_test_split(
        tokenized_datasets, "train", config.number_of_training_samples, config.seed
    )
    small_test_dataset = train_and_test_split(
        tokenized_datasets, "test", config.number_of_test_samples, config.seed
    )

    model_result = train_model(
        small_train_dataset,
        small_test_dataset,
        training_args,
    )

    return model_result


@sematic.func
def load_yelp_dataset() -> DatasetDict:
    return load_dataset("yelp_review_full")


def tokenize_function(examples):
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    return tokenizer(examples["text"], padding="max_length", truncation=True)


@sematic.func
def tokenize_dataset(dataset: DatasetDict) -> DatasetDict:
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    return tokenized_datasets


@sematic.func
def train_and_test_split(
    tokenized_datasets: DatasetDict, dataset_key: str, select_range: int, seed: int
) -> Dataset:
    return tokenized_datasets[dataset_key].shuffle(seed).select(range(select_range))


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    metric = load_metric("accuracy")
    return metric.compute(predictions=predictions, references=labels)


@sematic.func
def train_model(
    train_dataset: Dataset,
    eval_dataset: Dataset,
    training_args: TrainingArguments,
) -> DistilBertForSequenceClassification:
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=5
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    return model
