# Standard Library
from dataclasses import dataclass
from typing import Any, Dict, Union

# Third-party
import pytest

# Sematic
from sematic.types.types.huggingface.stored_model import StoredModel

# get_base_model
# save_pretrained

_MOCK_STORAGE = {}


@pytest.fixture
def mock_storage():
    global _MOCK_STORAGE
    _MOCK_STORAGE = {}
    try:
        yield
    finally:
        _MOCK_STORAGE = {}


@dataclass
class Model:
    state: str

    def save_pretrained(self, path: str):
        _MOCK_STORAGE[path] = self.state

    @classmethod
    def from_pretrained(
        cls, path: str, device_map: Union[str, Dict[str, Any]]
    ) -> "Model":
        return Model(state=_MOCK_STORAGE[path])


@dataclass
class PeftModel:
    state: str
    base_model: Model

    def save_pretrained(self, path: str):
        _MOCK_STORAGE[path] = self.state

    @classmethod
    def from_pretrained(
        cls, base_model: Model, path: str, device_map: Union[str, Dict[str, Any]]
    ) -> "Model":
        return PeftModel(state=_MOCK_STORAGE[path], base_model=base_model)

    def get_base_model(self) -> Model:
        return self.base_model


def test_store_load_non_peft(mock_storage):
    storage_path = "/some/path/for/model"
    model = Model(state="foo")
    stored_model = StoredModel.store(model, storage_path)
    loaded = stored_model.load(device_map="auto")
    assert loaded == model


def test_store_load_peft(mock_storage):
    storage_path = "/some/path/for/model"
    base_model = Model(state="foo")
    peft_model = PeftModel(state="bar", base_model=base_model)
    stored_model = StoredModel.store(peft_model, storage_path)
    loaded = stored_model.load(device_map="auto")
    assert loaded == peft_model
