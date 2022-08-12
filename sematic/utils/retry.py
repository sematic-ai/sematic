# Credited to invl: https://github.com/invl/retry/blob/master/retry/api.py
# adapted to follow our linting and docstring style. Used here instead
# of depending on that library to avoid taking on another explicit
# third-party dep.
# Retrieved on 08/10/22, original source code uses the Apache 2
# license.

# Standard Library
import logging
import random
import time
from functools import partial, wraps

logging_logger = logging.getLogger(__name__)


def decorator(caller):
    """Turns caller into a decorator.
    Unlike decorator module, function signature is not preserved.

    Parameters
    ----------
    caller: caller(f, *args, **kwargs)
    """

    def decor(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return caller(f, *args, **kwargs)

        return wrapper

    return decor


def __retry_internal(
    f,
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=None,
    backoff=1,
    jitter=0,
    logger=logging_logger,
):
    """Executes a function and retries it if it failed.

    Parameters
    ----------
    f:
        the function to execute.
    exceptions:
        an exception or a tuple of exceptions to catch. default: Exception.
    tries:
        the maximum number of attempts. default: -1 (infinite).
    delay:
        initial delay between attempts. default: 0.
    max_delay:
        the maximum value of delay. default: None (no limit).
    backoff:
        multiplier applied to delay between attempts. default: 1 (no backoff).
    jitter:
        extra seconds added to delay between attempts. default: 0. fixed if a number,
        random if a range tuple (min, max).
    logger:
        logger.warning(fmt, error, delay) will be called on failed attempts.
        default: retry.logging_logger. if None, logging is disabled.

    Returns
    -------
    the result of the f function.
    """
    _tries, _delay = tries, delay
    while _tries:
        try:
            return f()
        except exceptions as e:
            _tries -= 1
            if not _tries:
                raise

            if logger is not None:
                logger.warning("%s, retrying in %s seconds...", e, _delay)

            time.sleep(_delay)
            _delay *= backoff

            if isinstance(jitter, tuple):
                _delay += random.uniform(*jitter)
            else:
                _delay += jitter

            if max_delay is not None:
                _delay = min(_delay, max_delay)


def retry(
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=None,
    backoff=1,
    jitter=0,
    logger=logging_logger,
):
    """Returns a retry decorator.

    Parameters
    ----------
    exceptions:
        an exception or a tuple of exceptions to catch. default: Exception.
    tries:
        the maximum number of attempts. default: -1 (infinite).
    delay:
        initial delay between attempts. default: 0.
    max_delay:
        the maximum value of delay. default: None (no limit).
    backoff:
        multiplier applied to delay between attempts. default: 1 (no backoff).
    jitter:
        extra seconds added to delay between attempts. default: 0.
        fixed if a number, random if a range tuple (min, max)
    logger:
        logger.warning(fmt, error, delay) will be called on failed attempts.
        default: retry.logging_logger. if None, logging is disabled.

    Returns
    -------
    A retry decorator.
    """

    @decorator
    def retry_decorator(f, *fargs, **fkwargs):
        args = fargs if fargs else list()
        kwargs = fkwargs if fkwargs else dict()
        return __retry_internal(
            partial(f, *args, **kwargs),
            exceptions,
            tries,
            delay,
            max_delay,
            backoff,
            jitter,
            logger,
        )

    return retry_decorator


def retry_call(
    f,
    fargs=None,
    fkwargs=None,
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=None,
    backoff=1,
    jitter=0,
    logger=logging_logger,
):
    """Calls a function and re-executes it if it failed.

    Parameters
    ----------
    f:
        the function to execute.
    fargs:
        the positional arguments of the function to execute.
    fkwargs:
        the named arguments of the function to execute.
    exceptions:
        an exception or a tuple of exceptions to catch. default: Exception.
    tries:
        the maximum number of attempts. default: -1 (infinite).
    delay:
        initial delay between attempts. default: 0.
    max_delay:
        the maximum value of delay. default: None (no limit).
    backoff:
        multiplier applied to delay between attempts. default: 1 (no backoff).
    jitter:
        extra seconds added to delay between attempts. default: 0.
        fixed if a number, random if a range tuple (min, max)
    logger:
        logger.warning(fmt, error, delay) will be called on failed attempts.
        default: retry.logging_logger. if None, logging is disabled.

    Returns
    --------
    the result of the f function.
    """
    args = fargs if fargs else list()
    kwargs = fkwargs if fkwargs else dict()
    return __retry_internal(
        partial(f, *args, **kwargs),
        exceptions,
        tries,
        delay,
        max_delay,
        backoff,
        jitter,
        logger,
    )
