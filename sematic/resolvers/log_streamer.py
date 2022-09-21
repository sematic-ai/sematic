# Standard Library
import multiprocessing
import threading
import time
import os

# Sematic
from sematic.storage import set_from_file
from sematic.utils.retry import retry


def stream_logs_to_remote_from_file(
    file_path: str, upload_interval_seconds: int, remote_prefix: str
):
    if remote_prefix.endswith("/"):
        remote_prefix = remote_prefix[:-1]
    while True:
        do_upload(file_path, remote_prefix)
        time.sleep(upload_interval_seconds)


def stream_logs_to_stdout_from_file(file_path: str, original_stdout: int):
    os.write(original_stdout, "Streaming to original stdout...".encode("utf8"))
    with open(file_path, "rb") as fp:
        for line in fp:
            os.write(original_stdout, line)


@retry(tries=3, delay=5)
def do_upload(file_path: str, remote_prefix: str):
    remote = f"{remote_prefix}/{int(time.time() * 1000)}.log"
    print(f"Uploading {file_path} to {remote}")
    set_from_file(remote, file_path)


def start_log_streamers_in_process(
    file_path: str, upload_interval_seconds: int, remote_prefix: str, original_stdout: int
):
    thread = threading.Thread(target=lambda: stream_logs_to_stdout_from_file(file_path, original_stdout))
    thread.setDaemon(True)
    thread.start()
    stream_logs_to_remote_from_file(file_path, upload_interval_seconds, remote_prefix)


def start_log_streamers_out_of_process(
    file_path: str, upload_interval_seconds: int, remote_prefix: str, original_stdout: int
):
    kwargs = dict(
        file_path=file_path,
        upload_interval_seconds=upload_interval_seconds,
        remote_prefix=remote_prefix,
        original_stdout=original_stdout,
    )
    multiprocessing.Process(
        group=None,
        target=start_log_streamers_in_process,
        kwargs=kwargs,
        daemon=True,
    )
