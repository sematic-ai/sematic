import sematic
import numpy as np
import os

from datasets import load_dataset, load_metric, DatasetDict, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, DistilBertForSequenceClassification

os.environ["WANDB_DISABLED"] = "true"

pretrained_model_name = "distilbert-base-uncased"

tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name)

@sematic.func
def pipeline() -> DistilBertForSequenceClassification:
    """
    This is a basic example of using [HuggingFace DistilBERT 🤗](https://huggingface.co/docs/transformers/model_doc/distilbert) for next sentence prediction (NSP).
    """
    dataset = load_yelp_dataset()

    tokenized_datasets = tokenize_dataset(dataset)

    small_train_dataset = train_and_test_split(tokenized_datasets, "train", 20)
    small_test_dataset = train_and_test_split(tokenized_datasets, "test", 20)

    training_args = TrainingArguments(output_dir="test_trainer", evaluation_strategy="epoch")
    
    model = train_model(small_train_dataset, small_test_dataset, training_args)

    return model

@sematic.func
def load_yelp_dataset() -> DatasetDict:
    dataset = load_dataset("yelp_review_full")
    return dataset

def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True)

@sematic.func
def tokenize_dataset(dataset: DatasetDict) -> DatasetDict:
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    return tokenized_datasets

@sematic.func
def train_and_test_split(tokenized_datasets: DatasetDict, dataset_key: str, select_range: int) -> Dataset:
    return tokenized_datasets[dataset_key].shuffle(seed=42).select(range(select_range))

def compute_metrics(eval_pred):
    metric = load_metric("accuracy")

    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

@sematic.func
def train_model(train_dataset: Dataset, eval_dataset: Dataset, training_args: TrainingArguments) -> DistilBertForSequenceClassification:
    model = AutoModelForSequenceClassification.from_pretrained(pretrained_model_name, num_labels=5)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    return model