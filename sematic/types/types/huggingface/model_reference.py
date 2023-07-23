# Standard Library
import os
from dataclasses import dataclass
from typing import Optional

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
    local_override_dir:
        Local directory where the object is stored. If present the model
        should be loaded from here instead of loading from the HuggingFace hub.
    local_tokenizer_override_dir:
        Local directory where the tokenizer is stored. If present the
        tokenizer should be loaded from here instead of loading from the
        HuggingFace hub.
    """

    local_override_dir: Optional[str] = None
    local_tokenizer_override_dir: Optional[str] = None

    def load_reference(self) -> str:
        """The reference to pass into HuggingFace's from_pretrained to load the model

        Will use local_override_dir if present and that directory actually exists.
        """
        return self.repo_reference()
        if self.local_override_dir is not None and os.path.exists(
            self.local_override_dir
        ):
            return self.local_override_dir
        else:
            return self.repo_reference()

    def tokenizer_load_reference(self) -> str:
        """The reference to pass into HuggingFace's from_pretrained to load the tokenizer.

        Will use local_tokenizer_override_dir if present and that directory actually exists.
        """
        return self.repo_reference()
        if self.local_tokenizer_override_dir is not None and os.path.exists(
            self.local_tokenizer_override_dir
        ):
            return self.local_tokenizer_override_dir
        else:
            return self.repo_reference()
