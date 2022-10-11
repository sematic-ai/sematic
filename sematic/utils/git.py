"""
Utility for extracting details about the git workspace.
"""
# Standard Library
import inspect
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

# Third-party
import git  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class GitInfo:
    remote: Optional[str]
    branch: Optional[str]
    commit: Optional[str]
    dirty: Optional[bool]


def get_git_info(object_: Any):
    """
    Returns git repository details for a given Python object.
    """
    try:
        source = inspect.getsourcefile(object_)
        logger.debug(f"Found source file for {object_}: '{source}'")
    except Exception as e:
        logger.debug(f"Could not find source file for object '{object_}'", exc_info=e)
        return None

    try:
        repo = git.Repo(source, search_parent_directories=True)
        # when submitting a bazel script, the .git directory will be a symlink from the
        # bazel execroot to the source code workspace
        # this will mess up the dirty bit inspection, so we need to resolve the symlink
        if os.path.islink(repo.git_dir):
            resolved_git_dir = os.readlink(repo.git_dir)
            repo = git.Repo(resolved_git_dir, search_parent_directories=True)
    except Exception as e:
        logger.debug(f"Could not find git repo for source file '{source}'", exc_info=e)
        return None

    if repo.bare:
        logger.debug(f"Found bare git repo for source file '{source}'")
        return None

    return GitInfo(
        remote=_get_remote(repo),
        branch=_get_branch(repo),
        commit=_get_commit(repo),
        dirty=repo.is_dirty(),
    )


def _get_remote(repo: git.Repo):
    try:
        return repo.remote().config_reader.get_value("url", None)
    except Exception as e:
        logger.debug(f"Could not get remote from git repo '{repo}'", exc_info=e)
        return None


def _get_commit(repo: git.Repo):
    try:
        return repo.commit().hexsha
    except Exception as e:
        logger.debug(f"Could not get commit from git repo '{repo}'", exc_info=e)
        return None


def _get_branch(repo: git.Repo):
    try:
        return repo.active_branch.name
    except Exception:
        return "HEAD is detached"
