# Standard Library
from dataclasses import dataclass


@dataclass
class GitInfo:
    """
    Information about a git workspace.
    """

    remote: str
    branch: str
    commit: str
    dirty: bool
