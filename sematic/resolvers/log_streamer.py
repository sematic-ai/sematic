# Standard Library
import contextlib
import multiprocessing
import os
import stat
import sys
import time
import traceback
from typing import Callable, Optional

# Sematic
from sematic.config import KUBERNETES_POD_NAME_ENV_VAR
from sematic.storage import set_from_file
from sematic.utils.retry import retry
from sematic.utils.stdout import redirect_to_file

"""
An overview of how logging works:
- stdout and stderr are redirected to a file from the Sematic worker
- the Sematic worker on launch starts a child process that periodically
    uses our storage abstraction to upload the log file to persistent storage
- the name of the logs on the remote contain metadata about what run and job type
   the logs came from
- the server reads the logs from persistent storage for UI display
- it's safe to assume that the worker will have write access to the persistent storage
  because it's the same bucket used for artifacts.
"""


DEFAULT_LOG_UPLOAD_INTERVAL_SECONDS = 10


def _stream_logs_to_remote_from_file(
    file_path: str,
    upload_interval_seconds: int,
    remote_prefix: str,
    uploader: Callable[[str, str], None],
):
    """Execute infinite loop to periodically upload from file_path to remote storage

    Parameters
    ----------
    file_path:
        The path to the local file that's being uploaded
    upload_interval_seconds:
        The amount of time between the end of one upload and the start of the next
    remote_prefix:
        The prefix for the remote storage location where the log files will be kept.
        The actual file name will be unique for each upload, increasing monoatonically
        with time
    uploader:
        A callable to perform the upload. It will be given the path to upload from and
        the remote prefix as arguments.
    """
    while True:
        uploader(file_path, remote_prefix)
        time.sleep(upload_interval_seconds)


@retry(tries=3, delay=5)
def _do_upload(file_path: str, remote_prefix: str):
    """Upload a local file to remote storage

    Parameters
    ----------
    file_path:
        The path to the local file being uploaded
    remote_prefix:
        The prefix for the remote file. The full remote path will be
        this concatenated with `/<epoch timestamp>.log`.
    """
    if remote_prefix.endswith("/"):
        remote_prefix = remote_prefix[:-1]
    remote = f"{remote_prefix}/{int(time.time() * 1000)}.log"
    set_from_file(remote, file_path)


def _start_log_streamer_out_of_process(
    file_path: str,
    upload_interval_seconds: int,
    remote_prefix: str,
    uploader: Callable[[str, str], None],
) -> multiprocessing.Process:
    """Start a subprocess to periodically upload the log file to remote storage

    Note that the caller should always call do_upload before terminating to ensure
    that logs are not lost when the caller terminates between uploads.

    Parameters
    ----------
    file_path:
        The path to the local log file
    upload_interval_seconds:
        The interval between uploads.
    uploader:
        An optional custom uploader for the log data

    Returns
    -------
    The process doing the logging
    """
    kwargs = dict(
        file_path=file_path,
        upload_interval_seconds=upload_interval_seconds,
        remote_prefix=remote_prefix,
        uploader=uploader,
    )
    process = multiprocessing.Process(
        group=None,
        target=_stream_logs_to_remote_from_file,
        kwargs=kwargs,
        daemon=True,
    )
    process.start()
    return process


@contextlib.contextmanager
def ingested_logs(
    file_path: str,
    remote_prefix: str,
    upload_interval_seconds=DEFAULT_LOG_UPLOAD_INTERVAL_SECONDS,
    max_tail_bytes: int = 2**13,
    uploader: Optional[Callable[[str, str], None]] = None,
):
    """Code within context will have stdout/stderr (including subprocess) ingested

    The ingestion will use file_path as an on-disk cache to capture the logs to, and
    logs will be uploaded to remote storage with a storage path prefix given by
    remote_prefix.

    Parameters
    ----------
    file_path:
        The path to the local cached log file
    upload_interval_seconds:
        The amount of time between uploads
    remote_prefix:
        The prefix for the remote storage location where ingested logs live
    max_tail_bytes:
        The maximum number of bytes of logs to print to the original stdout
        when the context exits. To disable, set to <=0. Defaults to 8kb
    uploader:
        An optional override for uploading the log file.
    """
    # we will eventually want to switch to use a pipe instead of file as the
    # buffer the subprocess reads from:
    # https://stackoverflow.com/questions/73821235/python-file-truncate-with-one-writer-and-one-reader?noredirect=1#comment130351264_73821235
    uploader = uploader if uploader is not None else _do_upload

    pod_name = os.getenv(KUBERNETES_POD_NAME_ENV_VAR)
    if pod_name is not None:
        # print is appropriate here because we want to write to actual stdout,
        # with no logging machinary in between. This is *about* the logs. It
        # will be shown when somebody does `kubectl logs <pod name>` because
        # it will go to stdout before stdout gets redirected.
        print(
            f"To follow these logs, try:\n\t"
            f"kubectl exec -i {pod_name} -- tail -f {file_path}"
        )
    final_upload_error = None
    try:
        with redirect_to_file(file_path):
            process = _start_log_streamer_out_of_process(
                file_path,
                upload_interval_seconds=upload_interval_seconds,
                remote_prefix=remote_prefix,
                uploader=uploader,
            )
            try:
                yield
            except Exception:
                # make sure error is logged while logs are directed
                # for ingestion so the error gets ingested. Re-raise
                # so caller can handle/not as needed.
                traceback.print_exc()
                raise
            finally:
                process.terminate()

                # ensure there's a final log upload, and that it contains ALL the
                # contents of stdout and stderr before we redirect them back to their
                # originals.
                sys.stdout.flush()
                sys.stderr.flush()

                try:
                    uploader(file_path, remote_prefix)
                except Exception as e:
                    final_upload_error = e
    finally:
        # outermost try/finally is so we can tail logs to non-redirected stdout
        # even if the code raised an error
        if final_upload_error is not None:
            print(f"Error with final log upload: {final_upload_error}", file=sys.stderr)

        # Why is this tailing useful? Because in the situations where somebody
        # is triaging some weird, complicated failure mode, it will be really helpful to
        # have quick access to the last few lines of the logs directly when looking at
        # the pod's output, without having to go to remote storage. This is ESPECIALLY
        # true when the problem is something with the "normal" logging mechanisms, like
        # a failure to upload the logs to remote. Having *some* way to see what the code
        # was doing before it died will be essential.
        _tail_log_file(file_path, max_tail_bytes)


def _tail_log_file(file_path, max_tail_bytes, print_func=None):
    """Print the last lines of the log file.

    The code will quickly traverse to the correct file location rather than reading
    through the whole log.
    """
    print_func = print_func if print_func is not None else print
    if max_tail_bytes <= 0:
        return

    n_bytes_in_file = os.stat(file_path)[stat.ST_SIZE]
    with open(file_path, "r") as fp:
        print_func(
            "Showing the tail of the logs for reference. For complete "
            "logs, please use the UI."
        )
        start_byte = max(0, n_bytes_in_file - max_tail_bytes)
        if start_byte != 0:
            print_func(
                "\t\t.\n\t\t.\n\t\t."
            )  # vertical '...' to show there's truncation

        # Why seek rather than just iterate through lines until we're near the end?
        # because log files may be GBs in size, and we want this operation to be
        # a quick debugging aid, and not slow down container execution by a lot
        # while we actually read the whole file.
        fp.seek(start_byte)
        for line_number, line in enumerate(fp):
            if start_byte != 0 and line_number == 0:
                # we may have done a seek mid-line. skip the first line so we don't show
                # something partial.
                continue
            print_func(line, end="")
