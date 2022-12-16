# Sematic
from sematic.abstract_future import AbstractFuture
from sematic.utils.git import get_git_info


def get_git_sha_caching_namespace(root_future: AbstractFuture) -> str:
    """
    Returns a caching namespace based on the specified pipeline root Future func's source
    code git commit SHA.

    Must only be used when launching the Resolution from a development environment that is
    versioned by git! Otherwise, this will raise an exception, and the cache will not be
    used!

    When using this caching namespace, switching to another commit or locally editing the
    code would result in cache invalidation.

    Successive code edits will not invalidate the cache, as the dirty code status is only
    compared against the clean commit, and the actual contents of the code edits is not
    considered.

    Parameters
    ----------
    root_future: AbstractFuture
        The root Future of the pipeline for which to look up the code git commit status.

    Returns
    -------
    A caching namespace which contains the git commit SHA and the dirty code value.

    Raises
    ------
    ValueError
        If the git information could not be found.
    """
    git_info = get_git_info(root_future.calculator.func)  # type: ignore

    if git_info is None:
        func_fqpn = root_future.calculator.get_func_fqpn()  # type: ignore
        raise ValueError(f"Could not get git information for {func_fqpn}")

    return f"{git_info.commit}+{git_info.dirty}"
