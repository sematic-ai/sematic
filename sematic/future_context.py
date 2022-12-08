# Standard Library
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, List, Optional, Type

# To avoid a circular dependency of:
# future_context -> resolver -> future -> future_context
Resolver = Any

FUTURE_ALGEBRA_DOC_LINK = "https://docs.sematic.dev/diving-deeper/future-algebra"


@dataclass(frozen=True)
class PrivateContext:
    """Contextual info about the execution of the current function, not for end users.

    This informstion may be used by the Sematic framework itself, but is not intended
    for usage by users of Sematic.

    Attributes
    ----------
    resolver_class_path:
        The import path for the resolver being used.
    external_resources:
        Objects that represent external resources that can be used by futures.
        Note that this list may be added to or removed from over the course of
        one Sematic func execution, as 'with' blocks are entered and exited.
    """

    resolver_class_path: str

    # futures will pull from this context when they are being
    # instantiated
    external_resources: List["AbstractExternalResource"] = field(default_factory=list)

    def resolver_class(self) -> Type[Resolver]:
        module_name, resolver_name = self.resolver_class_path.rsplit(".", maxsplit=1)
        module = import_module(module_name)
        resolver_class = getattr(module, resolver_name, None)
        if resolver_class is None:
            raise ImportError(f"No class named '{resolver_name}' in {module_name}")
        return resolver_class


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
    """

    run_id: str
    root_id: str
    private: PrivateContext


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
    NotInSematicFuncError:
        If this function is called outside the execution of a Sematic function.
    """
    global _current_context
    if _current_context is None:
        raise NotInSematicFuncError(
            "context() must be called from within the execution of a Sematic function, "
            "in the root process that function was invoked from."
        )
    return _current_context


class NotInSematicFuncError(RuntimeError):
    pass


# Note: this helps resolve circular imports. Otherwise we'd have:
# future_context -> external_resource -> future_context
# this approach cuts the first dependency in the above
class AbstractExternalResource:
    def __enter__(self) -> "AbstractExternalResource":
        if len(context().private.external_resources) != 0:
            # See: https://github.com/sematic-ai/sematic/issues/388
            raise RuntimeError(
                f"Sematic currently only allows one 'with' block resource "
                f"to be active at a time. Already in context for "
                f"{context().private.external_resources[0]}, cannot enter "
                f"context for {self}"
            )
        context().private.external_resources.append(self)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        context().private.external_resources.remove(self)
