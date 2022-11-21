# Standard Library
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitInfo:
    """
    Information about a git workspace.
    """

    remote: Optional[str]
    branch: Optional[str]
    commit: Optional[str]
    dirty: Optional[bool]
