# Standard Library
import importlib
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type, Union

# Path suffixes to use for storage if the model is a peft model
_BASE_MODEL_SUFFIX = "base"
_PEFT_MODEL_SUFFIX = "peft"

# Path suffixes to use for storage if the model is not a peft model
_FULL_MODEL_SUFFIX = "full"


@dataclass(frozen=True)
class StoredModel:
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
    """

    path: str
    model_type: str
    peft_model_type: Optional[str] = None

    @classmethod
    def store(cls, model, directory: str) -> "StoredModel":
        directory = os.path.expanduser(directory)
        model_type: str = _type_to_str(type(model))
        peft_type: Optional[str] = None
        if hasattr(model, "get_base_model"):
            model.get_base_model().save_pretrained(
                os.path.join(directory, _BASE_MODEL_SUFFIX)
            )
            model.save_pretrained(os.path.join(directory, _PEFT_MODEL_SUFFIX))
            model_type = _type_to_str(type(model.get_base_model()))
            peft_type = _type_to_str(type(model))
        else:
            model.save_pretrained(os.path.join(directory, _FULL_MODEL_SUFFIX))

        return StoredModel(
            path=os.path.abspath(directory),
            model_type=model_type,
            peft_model_type=peft_type,
        )

    def load(self, device_map: Union[str, Dict[str, Any]] = "auto"):
        base_path = (
            _FULL_MODEL_SUFFIX if self.peft_model_type is None else _BASE_MODEL_SUFFIX
        )
        base_model_type = _type_from_str(self.model_type)
        model = base_model_type.from_pretrained(
            os.path.join(self.path, base_path),
            device_map=device_map,
        )
        if self.peft_model_type is None:
            return model

        peft_model_type = _type_from_str(self.peft_model_type)
        model = peft_model_type.from_pretrained(
            model,
            os.path.join(self.path, _PEFT_MODEL_SUFFIX),
            device_map=device_map,
        )
        return model


def _type_to_str(type_: Type[Any]) -> str:
    return f"{type_.__module__}.{type_.__name__}"


def _type_from_str(type_str: str) -> Type[Any]:
    module_path, type_name = type_str.rsplit(".", maxsplit=1)
    module = importlib.import_module(module_path)
    return getattr(module, type_name)
