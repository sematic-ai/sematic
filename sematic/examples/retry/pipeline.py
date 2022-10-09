"""
This example illustrate the usage of RetrySettings to
guarantee a function gets retried.
"""
# Standard Library
import logging
import random

# Sematic
import sematic


class SomeException(Exception):
    pass


@sematic.func(
    inline=True, retry=sematic.RetrySettings(exceptions=(SomeException,), retries=5)
)
def raise_exception() -> float:
    """
    A toy function to illustrate the retry mechanism
    """
    logging.basicConfig(level=logging.INFO)
    random_number = random.random()
    logging.info("Random number {}".format(random_number))
    if random_number < 0.1:
        return random_number

    logging.info("Raising exception")
    raise SomeException
