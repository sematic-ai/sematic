# Third-party
import pytest

# Sematic
from sematic.types.types.huggingface.model_reference import HuggingFaceModelReference


sha = "1111111111111111111111111111111111111111"

CONVERSION_CASES = [
    (
        HuggingFaceModelReference(owner=None, repo="my_repo", commit_sha=None),
        "my_repo",
    ),
    (
        HuggingFaceModelReference(owner=None, repo="my_repo", commit_sha=sha),
        "my_repo@1111111111111111111111111111111111111111",
    ),
    (
        HuggingFaceModelReference(owner="the_owner", repo="my_repo", commit_sha=None),
        "the_owner/my_repo",
    ),
    (
        HuggingFaceModelReference(owner="the_owner", repo="my_repo", commit_sha=sha),
        "the_owner/my_repo@1111111111111111111111111111111111111111",
    ),
]


@pytest.mark.parametrize(
    "as_ref, as_string",
    CONVERSION_CASES,
)
def test_to_from_string(as_ref: HuggingFaceModelReference, as_string: str):
    assert as_ref.to_string() == as_string
    assert HuggingFaceModelReference.from_string(as_string) == as_ref
