# Standard Library
from dataclasses import dataclass
from enum import Enum, unique
from typing import List, Tuple

# Third-party
from datasets import Dataset, load_dataset
from peft import LoraConfig, PeftModelForSeq2SeqLM, get_peft_model
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    PreTrainedTokenizerBase,
    Trainer,
    TrainingArguments,
)

# Sematic
from sematic.types.types.aws import S3Location


@unique
class ModelSize(Enum):
    small = "small"
    base = "base"
    large = "large"
    xl = "xl"
    xxl = "xxl"


@dataclass
class TrainingConfig:
    model_size: ModelSize
    lora_config: LoraConfig
    checkpoint_location: S3Location


@dataclass
class DatasetConfig:
    test_fraction: float


@dataclass
class EvaluationResults:
    continuations: List[Tuple[str, str]]


# TODO: move to hugging face module and give it a visualization
@dataclass
class HuggingFaceModelReference:
    owner: str
    repo: str

    @classmethod
    def from_string(cls, as_string: str) -> "HuggingFaceModelReference":
        owner, repo = as_string.rsplit("/", maxsplit=1)
        return HuggingFaceModelReference(owner=owner, repo=repo)

    def to_string(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass
class HuggingFaceDatasetReference:
    owner: str
    repo: str

    @classmethod
    def from_string(cls, as_string: str) -> "HuggingFaceDatasetReference":
        owner, repo = as_string.rsplit("/", maxsplit=1)
        return HuggingFaceDatasetReference(owner=owner, repo=repo)

    def to_string(self) -> str:
        return f"{self.owner}/{self.repo}"


def load_model(model_name):
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        device_map="auto",
    )
    return model


def load_tokenizer(model_name) -> PreTrainedTokenizerBase:
    return AutoTokenizer.from_pretrained(model_name)


def _finance_preprocess_function(examples, tokenizer):
    # data preprocessing
    text_column = "sentence"
    label_column = "text_label"
    max_length = 128
    output_token_max_length = 300
    inputs = examples[text_column]
    targets = examples[label_column]
    model_inputs = tokenizer(
        inputs,
        max_length=max_length,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )
    labels = tokenizer(
        targets,
        max_length=output_token_max_length,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )
    labels = labels["input_ids"]
    labels[labels == tokenizer.pad_token_id] = -100
    model_inputs["labels"] = labels
    return model_inputs


def prepare_data(
    dataset_config: DatasetConfig,
    tokenizer: PreTrainedTokenizerBase,
):
    dataset = load_dataset("financial_phrasebank", "sentences_allagree")
    dataset = dataset["train"].train_test_split(
        test_size=dataset_config.test_fraction,
    )
    dataset["validation"] = dataset["test"]
    del dataset["test"]

    classes = dataset["train"].features["label"].names
    dataset = dataset.map(
        lambda x: {"text_label": [classes[label] for label in x["label"]]},
        batched=True,
        num_proc=1,
    )
    processed_datasets = dataset.map(
        lambda example: _finance_preprocess_function(example, tokenizer),
        batched=True,
        num_proc=1,
        remove_columns=dataset["train"].column_names,
        load_from_cache_file=False,
        desc="Running tokenizer on dataset",
    )
    train_dataset = processed_datasets["train"]
    eval_dataset = processed_datasets["validation"]
    return train_dataset, eval_dataset


def train(
    model_name: str, train_config: TrainingConfig, train_data: Dataset
) -> PeftModelForSeq2SeqLM:
    model = load_model(model_name)
    model = get_peft_model(model, train_config.lora_config)
    return model


def evaluate(
    model: PeftModelForSeq2SeqLM,
    eval_dataset: Dataset,
    tokenizer: PreTrainedTokenizerBase,
) -> EvaluationResults:
    model.eval()
    results: List[Tuple[str, str]] = []
    temp = tokenizer("Hi my name is Josh", return_tensors="pt")
    eval_dataset.set_format(type="torch", columns=["input_ids", "attention_mask"])
    for i, row in enumerate(eval_dataset.iter(batch_size=1)):
        print(f"Eval sample {i}")
        if i >= 10:
            break
        eval_tokens = row["input_ids"]
        input_text = tokenizer.batch_decode(
            eval_tokens.detach().cpu().numpy(), skip_special_tokens=True
        )
        output_tokens = model.generate(input_ids=eval_tokens, max_new_tokens=500)
        output_text = tokenizer.batch_decode(
            output_tokens.detach().cpu().numpy(), skip_special_tokens=True
        )
        results.append((input_text[0], output_text[0]))
    return EvaluationResults(results)
