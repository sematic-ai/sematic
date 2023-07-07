# Standard Library
from dataclasses import dataclass, replace
from typing import Optional

# Sematic
from sematic.types.types.huggingface.reference import HuggingFaceReference


@dataclass(frozen=True)
class HuggingFaceDatasetReference(HuggingFaceReference):
    """A reference to a dataset on Hugging Face Hub.

    When represented as a string, has the format:
    [owner/]repo[:subset][@commit_sha]
    Pieces in square brackets are optional. Examples:
    the_owner/the_repo:the_subset@1234567890123456789012345678901234567890
    the_repo
    the_repo@1234567890123456789012345678901234567890

    Attributes
    ----------
    owner:
        The owner of the dataset repo. If this is set to None, the repo will be assumed to
        be owned by Hugging Face staff.
    repo:
        The dataset repo.
    subset:
        The subset of the dataset. If this is set to None, the reference is to the whole
        dataset.
    commit_sha:
        The commit sha of the specific dataset version to be used. If this is set to None,
        the reference is to the latest commit (which may change depending on when the
        reference is used).
    """

    subset: Optional[str] = None

    def to_string(self, full_dataset: bool = False) -> str:
        subset = None if full_dataset else self.subset
        return super(
            HuggingFaceDatasetReference, replace(self, subset=subset)
        ).to_string()
