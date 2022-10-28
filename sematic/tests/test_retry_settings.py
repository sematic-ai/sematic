# Standard Library
from typing import Optional, Tuple

import pytest

# Sematic
from sematic.retry_settings import RetrySettings
from sematic.utils.exceptions import ExceptionMetadata


class ParentError(Exception):
    pass


class Child1Error(ParentError):
    pass


class Child2Error(ParentError):
    pass


# for testing Diamond inheritance.
class GrandChildError(Child1Error, Child2Error):
    pass


@pytest.mark.parametrize(
    "matches, exception_metadata",
    (
        (
            True,
            ExceptionMetadata(
                name=ValueError.__name__,
                module=ValueError.__module__,
                repr="ValueError",
                ancestors=ExceptionMetadata.ancestors_from_exception(ValueError),
            ),
        ),
        (
            False,
            ExceptionMetadata(
                name=AttributeError.__name__,
                module=AttributeError.__module__,
                repr="AttributeError",
                ancestors=ExceptionMetadata.ancestors_from_exception(AttributeError),
            ),
        ),
    ),
)
def test_matches_exceptions(matches: bool, exception_metadata: ExceptionMetadata):
    retry_settings = RetrySettings(exceptions=(ValueError,), retries=1)

    assert retry_settings._matches_exceptions(exception_metadata) is matches


@pytest.mark.parametrize(
    "should_retry, exception_metadata_tuple, retry_settings, retry_count",
    (
        (
            True,
            (
                ExceptionMetadata(
                    name=ValueError.__name__,
                    module=ValueError.__module__,
                    repr="ValueError",
                    ancestors=ExceptionMetadata.ancestors_from_exception(ValueError),
                ),
            ),
            RetrySettings(exceptions=(ValueError,), retries=2),
            1,
        ),
        (
            False,
            (
                ExceptionMetadata(
                    name=Exception.__name__,
                    module=Exception.__module__,
                    repr="Exception",
                    ancestors=ExceptionMetadata.ancestors_from_exception(Exception),
                ),
            ),
            RetrySettings(exceptions=(ValueError,), retries=2),
            1,
        ),
        (
            False,
            (
                ExceptionMetadata(
                    name=ValueError.__name__,
                    module=ValueError.__module__,
                    repr="ValueError",
                    ancestors=ExceptionMetadata.ancestors_from_exception(ValueError),
                ),
            ),
            RetrySettings(exceptions=(ValueError,), retries=2),
            2,
        ),
        (
            False,
            (
                ExceptionMetadata(
                    name=ValueError.__name__,
                    module=ValueError.__module__,
                    repr="ValueError",
                    ancestors=ExceptionMetadata.ancestors_from_exception(ValueError),
                ),
            ),
            RetrySettings(exceptions=(ValueError,), retries=2),
            2,
        ),
        (
            True,
            (
                ExceptionMetadata(
                    name=Child1Error.__name__,
                    module=Child1Error.__module__,
                    repr="Child1Error",
                    ancestors=ExceptionMetadata.ancestors_from_exception(Child1Error),
                ),
            ),
            RetrySettings(exceptions=(ParentError,), retries=2),
            1,
        ),
        (
            True,
            (
                ExceptionMetadata(
                    name=GrandChildError.__name__,
                    module=GrandChildError.__module__,
                    repr="GrandChildError",
                    ancestors=ExceptionMetadata.ancestors_from_exception(
                        GrandChildError
                    ),
                ),
            ),
            RetrySettings(exceptions=(ParentError,), retries=2),
            1,
        ),
        (
            False,
            (),
            RetrySettings(exceptions=(ValueError,), retries=2),
            1,
        ),
        (
            False,
            (None,),
            RetrySettings(exceptions=(ValueError,), retries=2),
            1,
        ),
        (
            False,
            (None, None),
            RetrySettings(exceptions=(ValueError,), retries=2),
            1,
        ),
        (
            True,
            (
                None,
                ExceptionMetadata(
                    name=ValueError.__name__,
                    module=ValueError.__module__,
                    repr="ValueError",
                    ancestors=ExceptionMetadata.ancestors_from_exception(ValueError),
                ),
            ),
            RetrySettings(exceptions=(ValueError,), retries=2),
            1,
        ),
        (
            True,
            (
                ExceptionMetadata(
                    name=ValueError.__name__,
                    module=ValueError.__module__,
                    repr="ValueError",
                    ancestors=ExceptionMetadata.ancestors_from_exception(ValueError),
                ),
                ExceptionMetadata(
                    name=ValueError.__name__,
                    module=ValueError.__module__,
                    repr="ValueError",
                    ancestors=ExceptionMetadata.ancestors_from_exception(ValueError),
                ),
            ),
            RetrySettings(exceptions=(ValueError,), retries=2),
            1,
        ),
        (
            True,
            (
                ExceptionMetadata(
                    name=Exception.__name__,
                    module=Exception.__module__,
                    repr="Exception",
                    ancestors=ExceptionMetadata.ancestors_from_exception(Exception),
                ),
                ExceptionMetadata(
                    name=ValueError.__name__,
                    module=ValueError.__module__,
                    repr="ValueError",
                    ancestors=ExceptionMetadata.ancestors_from_exception(ValueError),
                ),
            ),
            RetrySettings(exceptions=(ValueError,), retries=2),
            1,
        ),
        (
            False,
            (
                ExceptionMetadata(
                    name=Exception.__name__,
                    module=Exception.__module__,
                    repr="Exception",
                    ancestors=ExceptionMetadata.ancestors_from_exception(Exception),
                ),
                ExceptionMetadata(
                    name=ValueError.__name__,
                    module=ValueError.__module__,
                    repr="ValueError",
                    ancestors=ExceptionMetadata.ancestors_from_exception(ValueError),
                ),
            ),
            RetrySettings(exceptions=(ValueError,), retries=2),
            2,
        ),
    ),
)
def test_should_retry(
    should_retry: bool,
    exception_metadata_tuple: Tuple[Optional[ExceptionMetadata]],
    retry_settings: RetrySettings,
    retry_count: int,
):
    retry_settings.retry_count = retry_count
    assert retry_settings.should_retry(*exception_metadata_tuple) is should_retry
