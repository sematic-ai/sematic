# Sematic
from sematic.abstract_future import AbstractFuture
from sematic.utils.git import get_git_info


def get_git_sha_caching_namespace(future: AbstractFuture) -> str:
    """
    Returns a caching namespace based on the specified Future func's source code git
    commit SHA.

    When using this caching namespace, switching to another commit or locally editing the
    code would result in cache invalidation.

    Successive code edits will not invalidate the cache, as the dirty code status is only
    compared against the clean commit, and the actual contents of the code edits is not
    considered.

    Parameters
    ----------
    future: AbstractFuture
        The Future for which to look up the code git commit status.

    Returns
    -------
    A caching namespace which contains the git commit SHA and the dirty code value, or a
    message saying the git info could not be sourced, in case this is not executed from a
    development environment.
    """
    git_info = get_git_info(future.calculator.func)  # type: ignore

    if git_info is None:
        return "no git commit info"

    return f"{git_info.commit}+{git_info.dirty}"
