# Standard Library
import sys
import traceback
from dataclasses import dataclass, field
from typing import List, Optional, Type, Union

# Sematic
from sematic.abstract_calculator import CalculatorError


@dataclass
class ExceptionMetadata:
    repr: str
    name: str
    module: str

    # defaults to empty list for backwards compatibility for 0.17.0
    ancestors: List[str] = field(default_factory=list)

    @classmethod
    def from_exception(cls, exception: Exception) -> "ExceptionMetadata":
        return ExceptionMetadata(
            repr=str(exception),
            name=exception.__class__.__name__,
            module=exception.__class__.__module__,
            ancestors=cls.ancestors_from_exception(exception),
        )

    @classmethod
    def ancestors_from_exception(
        cls, exception: Union[BaseException, Type[BaseException]]
    ) -> List[str]:
        """For an Exception, return a list of all its base classes that inherit from
        Exception.

        Parameters
        ----------
        exception:
            The exception or exception class whose ancestors should be retrieved

        Returns
        -------
        A list of all base classes (and their base classes, etc.) that inherit
        from Exception. They will be in no particular order.
        """
        if isinstance(exception, BaseException):
            exception_type = type(exception)
        else:
            exception_type = exception
        ancestors = []
        to_traverse = [exception_type]
        self_classpath = f"{exception_type.__module__}.{exception_type.__name__}"
        while len(to_traverse) > 0:
            class_ = to_traverse.pop()
            for base in class_.__bases__:
                if not issubclass(base, Exception):
                    # only interested in exception classes
                    continue
                classpath = f"{base.__module__}.{base.__name__}"
                if classpath not in ancestors and self_classpath != classpath:
                    ancestors.append(classpath)
                    to_traverse.append(base)
        return ancestors

    def is_instance_of(self, exception_type: Type[Exception]) -> bool:
        """Determine whether this exception corresponds to an instance of exception_type

        Parameters
        ----------
        exception_type:
           The type of the exception we are checking this against

        Returns
        -------
        True if this exception is an instance of the given type, False otherwise
        """
        matches_self = (
            self.name == exception_type.__name__
            and self.module == exception_type.__module__
        )
        if matches_self:
            return True
        classpath = f"{exception_type.__module__}.{exception_type.__name__}"
        return classpath in self.ancestors


def format_exception_for_run(
    exception: Optional[BaseException] = None,
) -> Optional[ExceptionMetadata]:
    """Format an exception trace into a string for usage in a run.

    Returns
    -------
    Optional[ExceptionMetadata]
        If an exceptions is found on the traceback, an `ExceptionMetadata` object is
        instantiated to describe it. If not, None is returned.
    """
    if exception is None:
        _, exception, __ = sys.exc_info()
        if exception is None:
            # the failure was caused by another issue,
            # not by an exception on the traceback
            return None

    if isinstance(exception, CalculatorError) and exception.__cause__ is not None:
        # Don't display to the user the parts of the stack from Sematic
        # resolver if the root cause was a failure in Calculator code.
        tb_exception = traceback.TracebackException.from_exception(exception.__cause__)
        repr_ = "\n".join(tb_exception.format())
        exception = exception.__cause__
    else:
        repr_ = traceback.format_exc()

    assert isinstance(exception, BaseException)

    return ExceptionMetadata(
        repr=repr_,
        name=exception.__class__.__name__,
        module=exception.__class__.__module__,
        ancestors=ExceptionMetadata.ancestors_from_exception(exception),
    )


class KubernetesError(Exception):
    """An error originated in external Kubernetes compute infrastructure."""

    pass


class ResolutionError(Exception):
    """The pipeline resolution has failed.

    Should only be generated to halt execution. Should not be handled.

    Parameters
    ----------
    exception_metadata:
        Metadata describing an exception which occurred during code execution
        (Pipeline, Resolver, Driver)
    external_exception_metadata:
        Metadata describing an exception which occurred in external compute
        infrastructure
    """

    def __init__(
        self,
        exception_metadata: Optional[ExceptionMetadata] = None,
        external_exception_metadata: Optional[ExceptionMetadata] = None,
    ):
        exception_msg = ResolutionError._make_metadata_msg(
            "\n\nPipeline failure:\n", exception_metadata
        )
        external_exception_msg = ResolutionError._make_metadata_msg(
            "\n\nExternal failure:\n", external_exception_metadata
        )

        self._msg = (
            "The pipeline resolution failed due to previous errors!"
            f"{exception_msg}{external_exception_msg}"
        )

        super(ResolutionError, self).__init__(self._msg)

    @staticmethod
    def _make_metadata_msg(
        msg_prefix: str, metadata: Optional[ExceptionMetadata]
    ) -> str:
        if metadata is not None and metadata.repr is not None:
            return f"{msg_prefix}{metadata.repr}"
        return ""
