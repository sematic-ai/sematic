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
    Returns git repository details for the current workspace.

    The following are tried, in order:
    - attempt to get the git repo of the workspace that contains the specified
    object's source code
    - attempt to get the bazel workspace git repo
    - attempt to get the current working directory's git repo
    """
    try:
        # if git is not installed on the user's system, this will fail to import
        # Third-party
        import git  # type: ignore
    except ImportError as e:
        logger.warn("Could not get git information", exc_info=e)
        return None

    # try to search the path ancestors of the given object's source code for a git repo
    try:
        source = inspect.getsourcefile(object_)
        logger.debug(f"Found source path for {object_}: '{source}'")
    except Exception as e:
        logger.debug(f"Could not find source path for object '{object_}'", exc_info=e)
        return None

    logger.debug(f"Trying source path of specified object: {source}")
    repo = _get_repo(git, source)

    # try to search the bazel workspace for a git repo
    if repo is None:
        source = os.getenv("BUILD_WORKSPACE_DIRECTORY")
        if source is None:
            logger.debug("Could not find $BUILD_WORKSPACE_DIRECTORY")
            return None

        logger.debug(f"Trying $BUILD_WORKSPACE_DIRECTORY: {source}")
        repo = _get_repo(git, source)

    # try to search the current working directory for a git repo
    if repo is None:
        try:
            source = os.getcwd()
        except Exception as e:
            logger.debug("Could not get current working directory", exc_info=e)
            return None

        logger.debug(f"Trying current working directory: {source}")
        repo = _get_repo(git, source)

    # give up
    if repo is None:
        return None

    if repo.bare:
        logger.debug(f"Found bare git repo in '{repo.git_dir}'")
        return None

    return GitInfo(
        remote=_get_remote(repo),
        branch=_get_branch(repo),
        commit=_get_commit(repo),
        dirty=repo.is_dirty(),
    )


def _get_repo(git: Any, source: Any) -> Optional["Repo"]:  # type: ignore # noqa: F821
    try:
        repo = git.Repo(source, search_parent_directories=True)
        # when submitting a bazel script, the .git directory will be a symlink from the
        # bazel execroot to the source code workspace
        # this will mess up the dirty bit inspection, so we need to resolve the symlink
        if os.path.islink(repo.git_dir):
            resolved_git_dir = os.readlink(repo.git_dir)
            repo = git.Repo(resolved_git_dir, search_parent_directories=True)

        logger.debug(f"Found git repo in '{repo.git_dir}'")
        return repo

    except Exception as e:
        logger.debug(f"Could not find git repo for source path '{source}'", exc_info=e)
        return None


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
