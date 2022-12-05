# Standard Library
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Optional, Type


@dataclass(frozen=True)
class SematicContext:
    """Contextual information about the execution of the current Sematic function
    Attributes
    ----------
    id:
        The id of the future for the current execution. For cloud executions, this
        is equivalent to the id for the existing run.
    root_id:
        The id of the root future for a resolution. For cloud executions, this is
        equivalent to the id for the root run.
    resolver_class_path:
        The import path for the resolver being used.
    """

    id: str
    root_id: str
    resolver_class_path: str

    def resolver_class(self) -> Type[Any]:
        module_name, resolver_name = self.resolver_class_path.rsplit(".", maxsplit=1)
        module = import_module(module_name)
        resolver_class = getattr(module, resolver_name, None)
        if resolver_class is None:
            raise ImportError(f"No class named '{resolver_name}' in {module_name}")
        return resolver_class


_current_context: Optional[SematicContext] = None


@contextmanager
def set_context(ctx: SematicContext):
    """Context manager to execute a Sematic function with a global context enabled.

    This should only be called by Sematic itself, not by end-users.

    Parameters
    ----------
    ctx:
        The context that the function should be executed with
    """
    global _current_context

    # _current_context might not be None if a Sematic resolution is started
    # from within a Sematic func. This is not a pattern we encourage, but
    # shouldn't fail.
    prior_context = _current_context
    if not isinstance(ctx, SematicContext):
        raise ValueError(f"Expecting a Sematic context, got: {ctx}")
    _current_context = ctx
    try:
        yield
    finally:
        _current_context = prior_context


def context() -> SematicContext:
    """Get the current run context, including the active run id and root run id.

    This can be used if you wish to track information about a Sematic execution
    in an external system, and store it by an id that can link you back to the
    Sematic run. It should not be used to interact with the Sematic API directly.

    Returns
    -------
    The active context, if a Sematic function is currently executing. Otherwise
    it will raise an error.

    Raises
    ------
    RuntimeError:
        If this function is called outside the execution of a Sematic function.
    """
    global _current_context
    if _current_context is None:
        raise RuntimeError(
            "context() must be called from within the execution of a Sematic function, "
            "in the root process that function was invoked from."
        )
    return _current_context
