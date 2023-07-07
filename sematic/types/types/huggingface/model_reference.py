# Standard Library
from dataclasses import dataclass

# Sematic
from sematic.types.types.huggingface.reference import HuggingFaceReference


@dataclass(frozen=True)
class HuggingFaceModelReference(HuggingFaceReference):
    """A reference to a model on Hugging Face Hub.

    When represented as a string, has the format:
    [owner/]repo[@commit_sha]
    Pieces in square brackets are optional. Examples:
    the_owner/the_repo@1234567890123456789012345678901234567890
    the_owner/the_repo
    the_repo@1234567890123456789012345678901234567890

    Attributes
    ----------
    owner:
        The owner of the model repo. If this is set to None, the repo will be assumed to
        be owned by Hugging Face staff.
    repo:
        The model repo.
    commit_sha:
        The commit sha of the specific model version to be used. If this is set to None,
        the reference is to the latest commit (which may change depending on when the
        reference is used).
    """

    pass
