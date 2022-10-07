import pytest

# Sematic
from sematic.retry_settings import RetrySettings
from sematic.utils.exceptions import ExceptionMetadata


@pytest.mark.parametrize(
    "matches, exception_metadata",
    (
        (
            True,
            ExceptionMetadata(
                name=ValueError.__name__,
                module=ValueError.__module__,
                repr="ValueError",
            ),
        ),
        (
            False,
            ExceptionMetadata(
                name=AttributeError.__name__,
                module=AttributeError.__module__,
                repr="AttributeError",
            ),
        ),
    ),
)
def test_matches_exceptions(matches: bool, exception_metadata: ExceptionMetadata):
    retry_settings = RetrySettings(exceptions=(ValueError,), times=1)

    assert retry_settings._matches_exceptions(exception_metadata) is matches


@pytest.mark.parametrize(
    "should_retry, exception_metadata, retry_settings, retry_count",
    (
        (
            True,
            ExceptionMetadata(
                name=ValueError.__name__,
                module=ValueError.__module__,
                repr="ValueError",
            ),
            RetrySettings(exceptions=(ValueError,), times=2),
            1,
        ),
        (
            False,
            ExceptionMetadata(
                name=ValueError.__name__,
                module=ValueError.__module__,
                repr="ValueError",
            ),
            RetrySettings(exceptions=(ValueError,), times=2),
            2,
        ),
        (
            False,
            ExceptionMetadata(
                name=ValueError.__name__,
                module=ValueError.__module__,
                repr="ValueError",
            ),
            RetrySettings(exceptions=(ValueError,), times=2),
            2,
        ),
    ),
)
def test_should_retry(
    should_retry: bool,
    exception_metadata: ExceptionMetadata,
    retry_settings: RetrySettings,
    retry_count: int,
):
    retry_settings.retry_count = retry_count
    assert retry_settings.should_retry(exception_metadata) is should_retry
