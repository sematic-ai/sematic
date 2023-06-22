# Standard Library
from dataclasses import asdict, dataclass, replace
from enum import Enum, unique
from typing import List, Optional, Tuple, Type, Any

# Third-party
from datasets import Dataset, load_dataset
from peft import LoraConfig, PeftModelForSeq2SeqLM, get_peft_model
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedTokenizerBase,
    Trainer,
    TrainerCallback,
)
from transformers import TrainingArguments as HfTrainingArguments
import torch

# Sematic
from sematic.ee.metrics import MetricScope, log_metric
from sematic.types import (
    HuggingFaceDatasetReference,
    HuggingFaceModelReference,
    PromptResponse,
)


class LogMetricsCallback(TrainerCallback):
    def on_log(self, args, state, control, logs=None, **kwargs):
        log_metric("step", state.global_step)
        for metric, value in logs.items():
            log_metric(metric, value)


@unique
class ModelSelection(Enum):
    flan_small = "flan_small"
    flan_base = "flan_base"
    flan_large = "flan_large"
    flan_xl = "flan_xl"
    flan_xxl = "flan_xxl"
    falcon_7b = "falcon_7b"
    falcon_40b = "falcon_40b"

    @classmethod
    def from_model_reference(cls, ref: HuggingFaceModelReference) -> "ModelSelection":
        if "flan" in ref.repo:
            return ModelSelection[ref.repo.replace("flan-t5", "")]
        else:
            return ModelSelection[ref.repo.replace("-", "_")]

    def is_flan(self) -> bool:
        return self in {
            ModelSelection.flan_small,
            ModelSelection.flan_base,
            ModelSelection.flan_large,
            ModelSelection.flan_xl,
            ModelSelection.flan_xxl,
        }


@dataclass(frozen=True)
class ModelProperties:
    model_type: Type[Any]
    pad_token: Optional[str] = None
    trust_remote_code: bool = False
    load_in_8bit: bool = False
    torch_dtype: Optional[torch.dtype] = None


_FLAN_PROPS = ModelProperties(model_type=AutoModelForSeq2SeqLM)
_FALCON_PROPS = ModelProperties(
    model_type=AutoModelForCausalLM,
    pad_token="eos_token",
    trust_remote_code=True,
    load_in_8bit=True,
    torch_dtype=torch.bfloat16,
)

_MODEL_PROPERTIES = {
    ModelSelection.flan_small: _FLAN_PROPS,
    ModelSelection.flan_base: _FLAN_PROPS,
    ModelSelection.flan_large: _FLAN_PROPS,
    ModelSelection.flan_xl: _FLAN_PROPS,
    ModelSelection.flan_xxl: _FLAN_PROPS,
    ModelSelection.falcon_7b: _FALCON_PROPS,
    ModelSelection.falcon_40b: _FALCON_PROPS,
}


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
    logging_steps: int

    def to_hugging_face(self) -> HfTrainingArguments:
        return HfTrainingArguments(**asdict(self))


@dataclass
class TrainingConfig:
    model_selection: ModelSelection
    lora_config: LoraConfig
    training_arguments: TrainingArguments
    storage_directory: str


@dataclass
class DatasetConfig:
    max_output_length: int
    max_input_length: int
    dataset_ref: HuggingFaceDatasetReference
    text_column: str
    summary_column: str
    max_train_samples: Optional[int] = None
    max_test_samples: Optional[int] = None


@dataclass
class EvaluationResults:
    continuations: List[PromptResponse]


def load_model(model_name):
    model_props = _MODEL_PROPERTIES[ModelSelection.from_model_reference(
        HuggingFaceModelReference.from_string(model_name)
    )]
    model = model_props.model_type.from_pretrained(
        model_name,
        device_map="auto",
        trust_remote_code=model_props.trust_remote_code,
        load_in_8bit=model_props.load_in_8bit,
        torch_dtype=model_props.torch_dtype,
    )
    return model


def load_tokenizer(model_name) -> PreTrainedTokenizerBase:
    model_props = _MODEL_PROPERTIES[ModelSelection.from_model_reference(
        HuggingFaceModelReference.from_string(model_name)
    )]
    tokenizer = AutoTokenizer.from_pretrained(model_name, device_map="auto")
    if model_props.pad_token is not None:
        tokenizer.pad_token = getattr(tokenizer, model_props.pad_token)
    return tokenizer


def _docs_preprocess_function(examples, tokenizer, dataset_config):
    text_column = dataset_config.text_column
    label_column = dataset_config.summary_column
    max_length = dataset_config.max_input_length
    output_token_max_length = dataset_config.max_output_length
    inputs = [
        f"*Please summarize*: {ctx}. *Summary*: " for ctx in examples[text_column]
    ]
    targets = [target for target in examples[label_column]]
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
    dataset = load_dataset(
        dataset_config.dataset_ref.to_string(full_dataset=True),
        dataset_config.dataset_ref.subset,
    )
    if "validation" not in dataset:
        if "test" not in dataset:
            test_size = 0.1
            if (
                dataset_config.max_train_samples is not None
                and dataset_config.max_test_samples is not None
            ):
                test_size = dataset_config.max_test_samples / (
                    dataset_config.max_test_samples + dataset_config.max_train_samples
                )

            dataset = dataset["train"].train_test_split(test_size=test_size, seed=42)

        if "test" in dataset:
            dataset["validation"] = dataset["test"]
            del dataset["test"]

    if dataset_config.max_train_samples is not None:
        dataset["train"] = dataset["train"].select(
            range(dataset_config.max_train_samples)
        )
    if dataset_config.max_test_samples is not None:
        dataset["validation"] = dataset["validation"].select(
            range(dataset_config.max_test_samples)
        )

    processed_datasets = dataset.map(
        lambda example: _docs_preprocess_function(example, tokenizer, dataset_config),
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
        callbacks=[LogMetricsCallback()],
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
        eval_tokens = row["input_ids"]
        input_text = tokenizer.batch_decode(
            eval_tokens.detach().cpu().numpy(), skip_special_tokens=True
        )
        output_tokens = model.generate(input_ids=eval_tokens, max_new_tokens=500)
        output_text = tokenizer.batch_decode(
            output_tokens.detach().cpu().numpy(), skip_special_tokens=True
        )
        results.append(
            PromptResponse(sanitize(input_text[0]), sanitize(output_text[0]))
        )
    eval_results = EvaluationResults(results)
    return eval_results


def export_model(
    model: PeftModelForSeq2SeqLM,
    push_model_reference: HuggingFaceModelReference,
) -> HuggingFaceModelReference:
    commit = model.push_to_hub(push_model_reference.to_string(), use_auth_token=True)
    return replace(push_model_reference, commit_sha=commit.oid)


def sanitize(string: str):
    string = string.replace("NaN", "?")
    return string
