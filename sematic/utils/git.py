"""
Utility for extracting details about the git workspace.
"""
# Standard Library
import inspect
import logging
import os
from typing import Any, Optional

# Sematic
from sematic.db.models.git_info import GitInfo

logger = logging.getLogger(__name__)


def get_git_info(object_: Any) -> Optional["Repo"]:  # type: ignore # noqa: F821
    """
    Returns git repository details for a given Python object.
    """
    try:
        # if git is not installed on the user's system, this will fail to import
        import git  # type: ignore
    except ImportError as e:
        logger.warn("Could not get git information", exc_info=e)
        return None

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


def _get_remote(repo: "Repo") -> Optional[str]:  # type: ignore # noqa: F821
    try:
        return repo.remote().config_reader.get_value("url", None)
    except Exception as e:
        logger.debug(f"Could not get remote from git repo '{repo}'", exc_info=e)
        return None


def _get_commit(repo: "Repo") -> Optional[str]:  # type: ignore # noqa: F821
    try:
        return repo.commit().hexsha
    except Exception as e:
        logger.debug(f"Could not get commit from git repo '{repo}'", exc_info=e)
        return None


def _get_branch(repo: "Repo") -> Optional[str]:  # type: ignore # noqa: F821
    try:
        return repo.active_branch.name
    except Exception:
        return "HEAD is detached"
