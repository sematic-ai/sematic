# Standard Library
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import import_module
from typing import Optional, Type

# Sematic
from sematic.resolver import Resolver

FUTURE_ALGEBRA_DOC_LINK = "https://docs.sematic.dev/diving-deeper/future-algebra"


@dataclass(frozen=True)
class SematicContext:
    """Contextual information about the execution of the current Sematic function

    Attributes
    ----------
    run_id:
        The id of the future for the current execution. For cloud executions, this
        is equivalent to the id for the existing run.
    root_id:
        The id of the root future for a resolution. For cloud executions, this is
        equivalent to the id for the root run.
    resolver_class_path:
        The import path for the resolver being used.
    """

    run_id: str
    root_id: str
    resolver_class_path: str

    def resolver_class(self) -> Type[Resolver]:
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

    if _current_context is not None:
        raise RuntimeError(
            f"You have called .resolve() within a Sematic func. Usually people "
            f"do this when they have a future object and want it to be resolved to "
            f"an actual value in the middle of a Sematic func's body for usage "
            f"downstream. If this is your use-case, consider wrapping the downstream "
            f"logic in a new Sematic func and passing the unresolved future into it. "
            f"Sematic will ensure that the future is resolved before it starts the "
            f"new func. For more information, read {FUTURE_ALGEBRA_DOC_LINK}"
        )

    if not isinstance(ctx, SematicContext):
        raise ValueError(f"Expecting a `SematicContext`, got: {ctx}")
    _current_context = ctx

    try:
        yield
    finally:
        _current_context = None


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
