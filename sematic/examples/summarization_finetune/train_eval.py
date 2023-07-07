# Standard Library
import time
from dataclasses import asdict, dataclass, replace
from enum import Enum, unique
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party
import torch
from datasets import Dataset, load_dataset
from peft import LoraConfig, PeftModelForSeq2SeqLM, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    PreTrainedTokenizerBase,
    Trainer,
    TrainerCallback,
)
from transformers import TrainingArguments as HfTrainingArguments

try:
    # Third-party
    from trl import SFTTrainer
except ImportError:
    print("Training with SFTTrainer not supported. Please install trl.")
    SFTTrainer = Trainer

# Sematic
# Metrics logging is only available for Sematic ee users.
# from sematic.ee.metrics import MetricScope, log_metric
# from sematic.ee.metrics import MetricScope, log_metric
from sematic.types import (
    HuggingFaceDatasetReference,
    HuggingFaceModelReference,
    PromptResponse,
)

_SUMMARY_START_INDICATOR = "**Summary**:"
_CONTEXT_START_INDICATOR = "**Please Summarize**:"
_SUMMARY_END_INDICATOR = "**End**"


def log_metric(name: str, value: float) -> None:
    """Stand-in for Sematic's `log_metric` that prints to stdout.

    Sematic's log_metric is only available for EE users.
    """
    print(f"Metric '{name}': {value}")


class LogMetricsCallback(TrainerCallback):
    def on_log(self, args, state, control, logs=None, **kwargs):
        log_metric("step", state.global_step)
        for metric, value in logs.items():
            log_metric(metric, value)


class SftPeftCallback(TrainerCallback):
    def __init__(self):
        self.model = None
        super().__init__()

    def on_save(self, args, state, control, **kwargs):
        self.model = kwargs["model"]


@unique
class ModelType(Enum):
    seq_to_seq = "seq_to_seq"
    causal = "causal"


@unique
class ModelSelection(Enum):
    flan_small = "flan_small"
    flan_base = "flan_base"
    flan_large = "flan_large"
    flan_xl = "flan_xl"
    flan_xxl = "flan_xxl"
    gpt_j_6b = "gpt_j_6b"

    @classmethod
    def from_model_reference(cls, ref: HuggingFaceModelReference) -> "ModelSelection":
        if "flan" in ref.repo:
            return ModelSelection[ref.repo.replace("flan-t5-", "flan_")]
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
    model_type: ModelType
    pad_token: Optional[str] = None
    load_in_8bit: bool = False
    device_map: Optional[Union[str, Dict[str, Any]]] = "auto"


_FLAN_PROPS = ModelProperties(model_type=ModelType.seq_to_seq)
_GPTJ_PROPS = ModelProperties(
    model_type=ModelType.causal,
    pad_token="eos_token",
    device_map=None,
    load_in_8bit=True,
)

_MODEL_PROPERTIES = {
    ModelSelection.flan_small: _FLAN_PROPS,
    ModelSelection.flan_base: _FLAN_PROPS,
    ModelSelection.flan_large: _FLAN_PROPS,
    ModelSelection.flan_xl: _FLAN_PROPS,
    ModelSelection.flan_xxl: _FLAN_PROPS,
    ModelSelection.gpt_j_6b: _GPTJ_PROPS,
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
    save_strategy: str
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
    model_props = _MODEL_PROPERTIES[
        ModelSelection.from_model_reference(
            HuggingFaceModelReference.from_string(model_name)
        )
    ]
    auto_model_type = (
        AutoModelForSeq2SeqLM
        if model_props.model_type is ModelType.seq_to_seq
        else AutoModelForCausalLM
    )

    model = auto_model_type.from_pretrained(
        model_name,
        device_map=model_props.device_map,
        load_in_8bit=model_props.load_in_8bit,
    )

    return model


def load_tokenizer(model_name) -> PreTrainedTokenizerBase:
    model_props = _MODEL_PROPERTIES[
        ModelSelection.from_model_reference(
            HuggingFaceModelReference.from_string(model_name)
        )
    ]
    tokenizer = AutoTokenizer.from_pretrained(model_name, device_map="auto")
    if model_props.pad_token is not None:
        tokenizer.pad_token = getattr(tokenizer, model_props.pad_token)
    return tokenizer


def wrap_context(ctx: str) -> str:
    return f"{_CONTEXT_START_INDICATOR} {ctx}. {_SUMMARY_START_INDICATOR} "


def extract_summary(text: str) -> str:
    start_index = max(0, text.find(_SUMMARY_START_INDICATOR))
    end_indicator_index = text.find(_SUMMARY_END_INDICATOR)
    end_index = len(text) if end_indicator_index < 0 else end_indicator_index
    return text[start_index:end_index]


def _causal_preprocess_function(examples, tokenizer, dataset_config):
    text_column = dataset_config.text_column
    label_column = dataset_config.summary_column

    inputs = [
        f"{wrap_context(ctx)} {summary} {_SUMMARY_END_INDICATOR}"
        for ctx, summary in zip(examples[text_column], examples[label_column])
    ]

    return {"text": inputs}


def _seq_2_seq_preprocess_function(examples, tokenizer, dataset_config):
    text_column = dataset_config.text_column
    label_column = dataset_config.summary_column
    max_length = dataset_config.max_input_length
    output_token_max_length = dataset_config.max_output_length
    inputs = [wrap_context(ctx) for ctx in examples[text_column]]
    targets = [
        f"{target} {_SUMMARY_END_INDICATOR}" for target in examples[label_column]
    ]
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
    model_type: ModelType,
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

    def seq_2_seq_preprocessor(example):
        return _seq_2_seq_preprocess_function(example, tokenizer, dataset_config)

    def causal_preprocessor(example):
        return _causal_preprocess_function(example, tokenizer, dataset_config)

    processed_datasets = dataset.map(
        (
            seq_2_seq_preprocessor
            if model_type is ModelType.seq_to_seq
            else causal_preprocessor
        ),
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
    tokenizer: PreTrainedTokenizerBase,
) -> PeftModelForSeq2SeqLM:
    model_properties = _MODEL_PROPERTIES[
        ModelSelection.from_model_reference(
            HuggingFaceModelReference.from_string(model_name)
        )
    ]
    training_args = train_config.training_arguments.to_hugging_face()
    model = load_model(model_name)
    if model_properties.model_type is ModelType.causal:
        saver = SftPeftCallback()
        trainer = SFTTrainer(
            model=model,
            args=training_args,
            peft_config=train_config.lora_config,
            train_dataset=train_data,
            eval_dataset=eval_data,
            tokenizer=tokenizer,
            packing=False,
            dataset_text_field="text",
            callbacks=[LogMetricsCallback(), saver],
        )
        model.config.use_cache = False
        trainer.train()
        model = saver.model
    else:
        model = get_peft_model(model, train_config.lora_config)
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_data,
            eval_dataset=eval_data,
            callbacks=[LogMetricsCallback()],
        )
        model.config.use_cache = False
        trainer.train()

    return model


def extract_prompt(text: str, max_tokens: int) -> str:
    # We need to make sure the prompt to summarize
    # doesn't get truncated out. Rule of thumb is
    # that there are roughly 4 English chars per token
    # on average. So the number of chars should be
    # truncated to be a little less than 4x the max
    # number of tokens, with enough space for
    # the Summarize prompt. We can go with 3.5x to
    # provide some margin for error.
    def trim_context(context):
        truncated = context[: int(3.5 * max_tokens) - len(_SUMMARY_START_INDICATOR)]
        if truncated == context:
            return context

        return truncated

    summary_start_start = text.find(_SUMMARY_START_INDICATOR)
    truncated = trim_context(text[:summary_start_start])
    result = f"{truncated} {_SUMMARY_START_INDICATOR}"
    return result


def _run_eval_tokenizer(examples, tokenizer, max_tokens):
    inputs = examples["text"]
    model_inputs = tokenizer(
        inputs,
        max_length=max_tokens,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )
    return model_inputs


def evaluate(
    model: PeftModelForSeq2SeqLM,
    eval_dataset: Dataset,
    tokenizer: PreTrainedTokenizerBase,
    model_type: ModelType,
    dataset_config: DatasetConfig,
) -> EvaluationResults:
    model.eval()
    results: List[Tuple[str, str]] = []
    model.config.use_cache = True
    if model_type is ModelType.causal:
        eval_dataset = eval_dataset.map(
            lambda example: {
                "text": extract_prompt(example["text"], dataset_config.max_input_length)
            },
            batched=False,
            num_proc=1,
            desc="Extracting eval prompts",
        )
        eval_dataset = eval_dataset.map(
            lambda examples: _run_eval_tokenizer(
                examples, tokenizer, dataset_config.max_input_length
            ),
            batched=True,
            num_proc=1,
            remove_columns=["text"],
            desc="Tokenizing eval prompts",
        )
    eval_dataset.set_format(type="torch", columns=["input_ids", "attention_mask"])

    started = time.time()
    for i, row in enumerate(eval_dataset.iter(batch_size=1)):
        seconds_since_start = int(time.time() - started)
        print(f"Eval sample {i} (after {seconds_since_start} s)")
        eval_tokens = row["input_ids"]
        input_text, output_text = evaluate_single_text(
            model,
            tokenizer,
            model_type,
            dataset_config.max_output_length,
            eval_tokens[0],
        )
        results.append(PromptResponse(sanitize(input_text[0]), sanitize(output_text)))
    eval_results = EvaluationResults(results)
    return eval_results


def evaluate_single_text(
    model, tokenizer, model_type, max_new_tokens, eval_tokens=None, eval_text=None
) -> Tuple[str, str]:
    if eval_tokens is None and eval_text is None:
        raise ValueError("One of eval_tokens or eval_text must be provided.")
    if eval_tokens is not None and eval_text is not None:
        raise ValueError("Only one of eval_tokens or eval_text must be provided.")

    if eval_text is not None:
        eval_tokens = torch.tensor(
            tokenizer(
                [eval_text],
                max_length=max_new_tokens,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            )[0].ids
        )
    else:
        eval_text = tokenizer.batch_decode(
            torch.unsqueeze(eval_tokens, 0).detach().cpu().numpy(),
            skip_special_tokens=True,
        )[0]

    output_tokens = model.generate(
        input_ids=torch.unsqueeze(eval_tokens, 0),
        max_new_tokens=max_new_tokens,
        pad_token_id=tokenizer.pad_token_id,
    )
    output_text = tokenizer.batch_decode(
        output_tokens.detach().cpu().numpy(), skip_special_tokens=True
    )
    if model_type is ModelType.causal:
        # Causal ML models extend the input. In our case, we want to
        # consider the "response" to only be the new part, not counting
        # the input.
        output_text = [output_text[0].replace(eval_text, "", 1)]
    return eval_text, output_text[0]


def export_model(
    model: PeftModelForSeq2SeqLM,
    push_model_reference: HuggingFaceModelReference,
) -> HuggingFaceModelReference:
    commit = model.push_to_hub(push_model_reference.to_string(), use_auth_token=True)
    return replace(push_model_reference, commit_sha=commit.oid)


def sanitize(string: str):
    string = string.replace("NaN", "?")
    return string
