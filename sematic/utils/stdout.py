# Standard Library
import os
import sys
from contextlib import contextmanager

# code adapted from: https://stackoverflow.com/a/22434262/2540669


def _fileno(file_or_fd):
    fd = getattr(file_or_fd, "fileno", lambda: file_or_fd)()
    if not isinstance(fd, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd


@contextmanager
def redirect_to_file(file_path: str):
    stdout = sys.stdout
    stderr = sys.stderr
    stdout_fd = _fileno(stdout)
    stderr_fd = _fileno(stderr)
    # copy stdout_fd before it is overwritten
    with os.fdopen(os.dup(stdout_fd), "wb") as stdout_copied:
        stdout.flush()  # flush library buffers that dup2 knows nothing about

        with os.fdopen(os.dup(stderr_fd), "wb") as stderr_copied:
            stderr.flush()

            with open(file_path, "wb") as to_file:
                os.dup2(to_file.fileno(), stdout_fd)
                os.dup2(to_file.fileno(), stderr_fd)
            try:
                yield  stdout_copied # allow code to be run with the redirected stdout
            finally:
                # restore stdout & stderr to previous values
                # NOTE: dup2 makes stdout_fd inheritable unconditionally
                stdout.flush()
                stderr.flush()
                os.dup2(stdout_copied.fileno(), stdout_fd)
                os.dup2(stderr_copied.fileno(), stderr_fd)
