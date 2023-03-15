# Standard Library
from unittest.mock import MagicMock

# Third-party
import pytest
import torch

# Sematic
from sematic.ee.plugins.external_resource.ray.checkpoint import (
    summarize_ray_torch_checkpoint,
)


class SomethingRandom:
    pass


SUMMARY_CASES = [
    ({}, "TorchCheckpoint:\n"),
    ({"model": None}, "TorchCheckpoint:\n"),
    (
        {"model": {"foo": SomethingRandom()}},
        "TorchCheckpoint:\n" "foo: SomethingRandom",
    ),
    (
        {
            "model": {
                "foo": SomethingRandom(),
                "lllllooooonnnggg_keeeyyy": SomethingRandom(),
            }
        },
        "TorchCheckpoint:\n"
        "foo                     : SomethingRandom\n"
        "lllllooooonnnggg_keeeyyy: SomethingRandom",
    ),
    (
        {"model": {"foo": SomethingRandom(), "bar": torch.ones(3)}},
        "TorchCheckpoint:\n" "foo: SomethingRandom\n" "bar: tensor<float32>(3)",
    ),
    (
        {"model": {"foo": torch.ones(3, 4, 5, dtype=torch.int16)}},
        "TorchCheckpoint:\n" "foo: tensor<int16>(3x4x5)",
    ),
]


@pytest.mark.parametrize("checkpoint_dict, expected_summary", SUMMARY_CASES)
def test_summarize_ray_torch_checkpoint(checkpoint_dict, expected_summary):
    mock_checkpoint = MagicMock(name="mock_checkpoint")
    mock_checkpoint.to_dict.return_value = checkpoint_dict
    summary = summarize_ray_torch_checkpoint(mock_checkpoint, None)[0]["repr"]
    assert expected_summary == summary
