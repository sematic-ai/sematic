# Standard Library
from dataclasses import asdict, dataclass
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
)
from transformers import TrainingArguments
from transformers import TrainingArguments as HfTrainingArguments


@unique
class ModelSize(Enum):
    small = "small"
    base = "base"
    # TODO: can't post large/xl/xxl to the server
    # because when they're serialized as one blob they
    # are too large. This will have to wait for
    # implementing new serialization that allows
    # multiple blobs for models.
    # large = "large"
    # xl = "xl"
    # xxl = "xxl"


# works around: https://github.com/huggingface/transformers/issues/23958
@dataclass
class TrainingArguments:
    output_dir: str
    evaluation_strategy: str
    learning_rate: float
    gradient_accumulation_steps: int
    auto_find_batch_size: bool
    num_train_epochs: int
    save_steps: int
    save_total_limit: int

    def to_hugging_face(self) -> HfTrainingArguments:
        return HfTrainingArguments(**asdict(self))


@dataclass
class TrainingConfig:
    model_size: ModelSize
    lora_config: LoraConfig
    training_arguments: TrainingArguments


@dataclass
class DatasetConfig:
    test_fraction: float


@dataclass
class EvaluationResults:
    continuations: List[Tuple[str, str]]


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
    model_name: str,
    train_config: TrainingConfig,
    train_data: Dataset,
    eval_data: Dataset,
) -> PeftModelForSeq2SeqLM:
    model = load_model(model_name)
    model = get_peft_model(model, train_config.lora_config)
    trainer = Trainer(
        model=model,
        args=train_config.training_arguments.to_hugging_face(),
        train_dataset=train_data,
        eval_dataset=eval_data,
    )
    model.config.use_cache = False
    trainer.train()
    return model


def evaluate(
    model: PeftModelForSeq2SeqLM,
    eval_dataset: Dataset,
    tokenizer: PreTrainedTokenizerBase,
) -> EvaluationResults:
    model.eval()
    results: List[Tuple[str, str]] = []
    model.config.use_cache = True
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
