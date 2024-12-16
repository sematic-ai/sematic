# Standard Library
import re
from dataclasses import dataclass
from typing import Optional, Type, TypeVar


_NOT_RESERVED_CHARS = r"[^/@:]+"
_CAPTURE_OWNER = f"(?P<owner>{_NOT_RESERVED_CHARS})"
_CAPTURE_REPO = f"(?P<repo>{_NOT_RESERVED_CHARS})"
_CAPTURE_SUBSET = f"(?P<subset>{_NOT_RESERVED_CHARS})"
_CAPTURE_COMMIT = f"(?P<commit>{_NOT_RESERVED_CHARS})"
_REGEX = f"({_CAPTURE_OWNER}/)?{_CAPTURE_REPO}(:{_CAPTURE_SUBSET})?(@{_CAPTURE_COMMIT})?"
_COMPILED_REGEX = re.compile(_REGEX)

T = TypeVar("T")


@dataclass(frozen=True)
class HuggingFaceReference:
    """A reference to an object on Hugging Face Hub.

    When represented as a string, has the format:
    [owner/]repo[:subset][@commit_sha]
    Pieces in square brackets are optional. Examples:
    the_owner/the_repo:the_subset@1234567890123456789012345678901234567890
    the_repo
    the_repo@1234567890123456789012345678901234567890

    Attributes
    ----------
    owner:
        The owner of the repo. If this is set to None, the repo will be assumed to
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

    owner: Optional[str]
    repo: str
    commit_sha: Optional[str] = None
    local_override_dir: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.repo, str):
            raise ValueError(f"Repo must be provided. Got: {self.repo}")

    @classmethod
    def from_string(cls: Type[T], as_string: str) -> T:
        match = _COMPILED_REGEX.match(as_string)
        if match is None:
            raise ValueError(f"Improperly formatted reference: '{as_string}'")

        kwargs = {}
        kwargs["repo"] = match.group("repo")
        kwargs["owner"] = match.group("owner")
        if hasattr(cls, "subset"):
            kwargs["subset"] = match.group("subset")
        kwargs["commit_sha"] = match.group("commit")
        return cls(**kwargs)

    def to_string(self, full_dataset: bool = False) -> str:
        as_string = ""
        if self.owner is not None:
            as_string += f"{self.owner}/"
        as_string += self.repo
        if getattr(self, "subset", None) is not None:
            as_string += f":{self.subset}"  # type: ignore
        if self.commit_sha is not None:
            as_string += f"@{self.commit_sha}"
        return as_string

    def repo_reference(self) -> str:
        as_string = ""
        if self.owner is not None:
            as_string += f"{self.owner}/"
        as_string += self.repo
        return as_string
