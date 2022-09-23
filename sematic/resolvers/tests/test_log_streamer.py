import sys
import pathlib
import tempfile
import time

from sematic.resolvers.log_streamer import ingested_logs, _tail_log_file

def test_ingested_logs():
    with tempfile.NamedTemporaryFile() as log_file:
        remote_prefix = "foo/bar"
        upload_interval = 0.1
        with ingested_logs(log_file.name, upload_interval_seconds=upload_interval, remote_prefix=remote_prefix, uploader=mock_uploader):
            print("From stdout")
            print("From stderr", file=sys.stderr)
            time.sleep(20 * upload_interval)  # ensure at least one upload happens before final flush
            print("From stdout late")
            print("From stderr late", file=sys.stderr)
    
    upload_number = 0
    uploads = []
    while pathlib.Path(_upload_path(log_file.name, upload_number)).exists():
        with open(_upload_path(log_file.name, upload_number), "r") as upload:
            uploads.append(list(upload))
        upload_number += 1

    assert len(uploads) > 1  # should be at least one timed, and the final flush

    # first upload should have only contained early writes
    assert uploads[0] == [
        f"{remote_prefix}\n",
        "From stdout\n",
        "From stderr\n",
    ]

    # last upload should have everything
    assert uploads[-1] == [
        f"{remote_prefix}\n",
        "From stdout\n",
        "From stderr\n",
        "From stdout late\n",
        "From stderr late\n",
    ]


def test_ingested_logs_uncaught():
    raised = False
    started = time.time()
    message = "Uncaught error!"
    try:
        with tempfile.NamedTemporaryFile() as log_file:
            remote_prefix = "foo/bar"
            upload_interval = 100  # should exit early despite the long interval
            with ingested_logs(log_file.name, upload_interval_seconds=upload_interval, remote_prefix=remote_prefix, uploader=mock_uploader):
                raise ValueError(message)
    except ValueError:
        raised = True
    assert raised
    assert time.time() - started < upload_interval

    upload_number = 0
    uploads = []
    while pathlib.Path(_upload_path(log_file.name, upload_number)).exists():
        with open(_upload_path(log_file.name, upload_number), "r") as upload:
            uploads.append(list(upload))
        upload_number += 1

    assert len(uploads) == 1
    assert message in "\n".join(uploads[0])


def test_tail_log_file():
    printed = []
    def print_func(to_print, end="\n", **kwargs):
        printed.append(to_print + end)

    with tempfile.NamedTemporaryFile() as log_file:
        remote_prefix = "foo/bar"
        upload_interval = 0.1
        line_template = "This is line {}"
        n_lines = 100
        with ingested_logs(log_file.name, upload_interval_seconds=upload_interval, remote_prefix=remote_prefix, uploader=mock_uploader):
            for i in range(n_lines):
                print(line_template.format(i))
        _tail_log_file(log_file.name, max_tail_bytes=0, print_func=print_func)

        assert len(printed) == 0
        _tail_log_file(log_file.name, max_tail_bytes=3*len(line_template), print_func=print_func)
        assert len(printed) > 0
        assert printed[-1] == line_template.format(n_lines - 1)

def _upload_path(file_uploaded, upload_number):
    file_prefix = f"{file_uploaded}.uploaded_to"
    upload_path = f"{file_prefix}.{upload_number}"
    return upload_path


# Why use this rather than patched storage? Because the uploads happen from
# a subprocess, and patches/fixtures don't work in subprocesses
def mock_uploader(file_path, remote_prefix):
    remote_prefix = remote_prefix.encode("utf8")
    upload_number = 0
    while pathlib.Path(_upload_path(file_path, upload_number)).exists():
        upload_number += 1
    with open(_upload_path(file_path, upload_number), "wb") as record:
        record.write(remote_prefix + b"\n")
        with open(file_path, "rb") as log:
            for line in log:
                record.write(line)