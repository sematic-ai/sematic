# Standard Library
import signal
import sys
import time
from contextlib import contextmanager
from multiprocessing import Process
from typing import Any


@contextmanager
def stdout_spinner():
    """
    Prints a spinning character to stdout while execution is inside this context.
    """
    spinner_process = None

    try:
        spinner_process = Process(target=_print_spinner)
        spinner_process.start()

        yield

    finally:
        if spinner_process is not None:
            try:
                spinner_process.terminate()
                spinner_process.join(timeout=5)
                if spinner_process.is_alive():
                    spinner_process.kill()

            except Exception:
                pass


def _print_spinner() -> None:
    """
    Prints a spinning character to stdout.

    This is meant to be used in a different process. Execution terminates when the process
    receives a `SIGTERM` signal.
    """
    do_spin = True

    def _handler(_: Any, __: Any) -> None:
        nonlocal do_spin
        do_spin = False

    signal.signal(signal.SIGTERM, _handler)

    while do_spin:
        for char in "\\|/-":
            print(char)
            time.sleep(0.1)
            sys.stdout.write("\033[F\033[K")
            sys.stdout.flush()
            if not do_spin:
                break
