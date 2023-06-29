# Standard Library
import importlib
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type, Union

from sematic.types.types.huggingface.model_reference import HuggingFaceModelReference

# Path suffixes to use for storage if the model is a peft model
_BASE_MODEL_SUFFIX = "base"
_PEFT_MODEL_SUFFIX = "peft"

# Path suffixes to use for storage if the model is not a peft model
_FULL_MODEL_SUFFIX = "full"


@dataclass(frozen=True)
class HuggingFaceStoredModel:
    """A HuggingFace model stored in storage.

    May be a peft fine-tuning of a model.

    Attributes
    ----------
    path:
        The storage path to the model. Currently must be local storage.
    model_type:
        The type of the model. If the model is a peft model, this
        is the type of the base model.
    peft_model_type:
        The type of the peft model. If the model is not a peft model,
        this is None.
    base_model_reference:
        This parameter ONLY applies for Peft models. By default, the base model
        for Peft models is stored and retrieved to/from the provided storage path.
        If this parameter is set, however, the base model will NOT be stored, and
        will be retrieved from Hugging Face Hub. 
    """

    path: str
    model_type: str
    peft_model_type: Optional[str] = None
    base_model_reference: Optional[HuggingFaceModelReference] = None

    @classmethod
    def store(cls, model, directory: str, base_model_reference: Optional[HuggingFaceModelReference]=None) -> "HuggingFaceStoredModel":
        directory = os.path.expanduser(directory)
        model_type: str = _type_to_str(type(model))
        peft_type: Optional[str] = None
        if hasattr(model, "get_base_model"):
            if base_model_reference is None:
                model.get_base_model().save_pretrained(
                    os.path.join(directory, _BASE_MODEL_SUFFIX)
                )
            model.save_pretrained(os.path.join(directory, _PEFT_MODEL_SUFFIX))
            model_type = _type_to_str(type(model.get_base_model()))
            peft_type = _type_to_str(type(model))
        else:
            model.save_pretrained(os.path.join(directory, _FULL_MODEL_SUFFIX))

        return HuggingFaceStoredModel(
            path=os.path.abspath(directory),
            model_type=model_type,
            peft_model_type=peft_type,
            base_model_reference=base_model_reference,
        )

    def load(self, **from_pretrained_kwargs):
        base_path = (
            _FULL_MODEL_SUFFIX if self.peft_model_type is None else _BASE_MODEL_SUFFIX
        )
        base_model_type = _type_from_str(self.model_type)
        if self.base_model_reference is not None:
            commit = self.base_model_reference.commit_sha
            model = base_model_type.from_pretrained(
                self.base_model_reference.repo_reference(),
                revision="main" if commit is None else commit,
                **from_pretrained_kwargs,
            )
        else:
            model = base_model_type.from_pretrained(
                os.path.join(self.path, base_path),
                **from_pretrained_kwargs,
            )
        if self.peft_model_type is None:
            return model

        peft_model_type = _type_from_str(self.peft_model_type)
        model = peft_model_type.from_pretrained(
            model,
            os.path.join(self.path, _PEFT_MODEL_SUFFIX),
            **from_pretrained_kwargs,
        )
        return model


def _type_to_str(type_: Type[Any]) -> str:
    return f"{type_.__module__}.{type_.__name__}"


def _type_from_str(type_str: str) -> Type[Any]:
    module_path, type_name = type_str.rsplit(".", maxsplit=1)
    module = importlib.import_module(module_path)
    return getattr(module, type_name)
