# This code is copied (and lightly modified) from
# https://github.com/benoitc/gunicorn/blob/add8a4c951f02a67ca1f81264e5c107fa68e6496/gunicorn/util.py#L471
# Standard Library
import os
import sys
from os import closerange


REDIRECT_TO = getattr(os, "devnull", "/dev/null")


def daemonize(enable_stdio_inheritance=False):
    """Standard daemonization of a process.

    http://www.faqs.org/faqs/unix-faq/programmer/faq/ section 1.7
    """
    if os.fork():
        os._exit(0)
    os.setsid()

    if os.fork():
        os._exit(0)

    os.umask(0o22)

    # In both the following any file descriptors above stdin
    # stdout and stderr are left untouched.

    if not enable_stdio_inheritance:
        # Remap all of stdin, stdout and stderr on to
        # /dev/null.

        closerange(0, 3)

        fd_null = os.open(REDIRECT_TO, os.O_RDWR)
        # PEP 446, make fd for /dev/null inheritable
        os.set_inheritable(fd_null, True)

        # expect fd_null to be always 0 here, but in-case not ...
        if fd_null != 0:
            os.dup2(fd_null, 0)

        os.dup2(fd_null, 1)
        os.dup2(fd_null, 2)

    else:
        fd_null = os.open(REDIRECT_TO, os.O_RDWR)

        # Always redirect stdin to /dev/null as we would
        # never expect to need to read interactive input.

        if fd_null != 0:
            os.close(0)
            os.dup2(fd_null, 0)

        # If stdout and stderr are still connected to
        # their original file descriptors we check to see
        # if they are associated with terminal devices.
        # When they are we map them to /dev/null so that
        # are still detached from any controlling terminal
        # properly. If not we preserve them as they are.
        #
        # If stdin and stdout were not hooked up to the
        # original file descriptors, then all bets are
        # off and all we can really do is leave them as
        # they were.

        def redirect(stream, fd_expect):
            try:
                fd = stream.fileno()
                if fd == fd_expect and stream.isatty():
                    os.close(fd)
                    os.dup2(fd_null, fd)
            except AttributeError:
                pass

        redirect(sys.stdout, 1)
        redirect(sys.stderr, 2)
