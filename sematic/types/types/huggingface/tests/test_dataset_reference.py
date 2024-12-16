# Third-party
import pytest

# Sematic
from sematic.types.types.huggingface.dataset_reference import (
    HuggingFaceDatasetReference,
)


sha = "1111111111111111111111111111111111111111"

CONVERSION_CASES = [
    (
        HuggingFaceDatasetReference(
            owner=None, repo="my_repo", subset=None, commit_sha=None
        ),
        "my_repo",
    ),
    (
        HuggingFaceDatasetReference(
            owner=None, repo="my_repo", subset=None, commit_sha=sha
        ),
        "my_repo@1111111111111111111111111111111111111111",
    ),
    (
        HuggingFaceDatasetReference(
            owner=None, repo="my_repo", subset="train", commit_sha=None
        ),
        "my_repo:train",
    ),
    (
        HuggingFaceDatasetReference(
            owner=None, repo="my_repo", subset="train", commit_sha=sha
        ),
        "my_repo:train@1111111111111111111111111111111111111111",
    ),
    (
        HuggingFaceDatasetReference(
            owner="the_owner", repo="my_repo", subset=None, commit_sha=None
        ),
        "the_owner/my_repo",
    ),
    (
        HuggingFaceDatasetReference(
            owner="the_owner", repo="my_repo", subset=None, commit_sha=sha
        ),
        "the_owner/my_repo@1111111111111111111111111111111111111111",
    ),
    (
        HuggingFaceDatasetReference(
            owner="the_owner", repo="my_repo", subset="train", commit_sha=None
        ),
        "the_owner/my_repo:train",
    ),
    (
        HuggingFaceDatasetReference(
            owner="the_owner", repo="my_repo", subset="train", commit_sha=sha
        ),
        "the_owner/my_repo:train@1111111111111111111111111111111111111111",
    ),
]


@pytest.mark.parametrize(
    "as_ref, as_string",
    CONVERSION_CASES,
)
def test_to_from_string(as_ref: HuggingFaceDatasetReference, as_string: str):
    assert as_ref.to_string() == as_string
    assert HuggingFaceDatasetReference.from_string(as_string) == as_ref
