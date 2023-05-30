from dataclasses import dataclass
from enum import Enum, unique

import sematic
from transformers import AutoModelForSeq2SeqLM, PreTrainedModel


@unique
class ModelSize(Enum):
    small = "small" 
    base = "base"
    large = "large"
    xl = "xl"
    xxl = "xxl"

# TODO: move to hugging face module and give it a visualization
@dataclass
class HuggingFaceModelReference:
    owner: str
    repo: str

    @classmethod
    def from_string(class, as_string: str) -> "HuggingFaceModel":
        owner, repo = as_string.rsplit("/", maxsplit=1)
        return HuggingFaceModel(owner=owner, repo=repo)

@dataclass
class ResultSummary:
    source_model: HuggingFaceModelReference


@dataclass
class TrainingConfig:
    model_size: ModelSize


@sematic.func
def pick_model(model_size: ModelSize) -> HuggingFaceModelReference:
    return HuggingFaceModelReference(
        owner="google",
        repo=f"flan-t5-{model_size.value}"
    )


@sematic.func
def summarize(source_model: HuggingFaceModelReference) -> ResultSummary:
    return ResultSummary(
        source_model=source_model,
    )


@sematic.func
def pipeline(training_config: TrainingConfig) -> ResultSummary:
    return pick_model(training_config.model_size)
