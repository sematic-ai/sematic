# Standard Library
import os
import sys
import tempfile

# Sematic
from sematic.utils.stdout import redirect_to_file, redirect_to_file_descriptor


def test_redirect_to_file():
    with tempfile.NamedTemporaryFile() as log_file:
        print("before")
        with redirect_to_file(log_file.name):
            print("during")
            print("from stderr", file=sys.stderr)

            # this seems to work when not using pytest.
            # Pytest is itself doing something weird with stdout though,
            # so it may be some conflict there.
            # subprocess.call(["python3", "-c", "print('from subprocess')"])
            print("during2")
        print("after")
        read_lines = list(line.decode("utf8").strip() for line in log_file)
    assert read_lines == [
        "during",
        "from stderr",
        # "from subprocess",  # see comment above
        "during2",
    ]


def test_redirect_to_file_descriptor():
    read_fd, write_fd = os.pipe()
    read_handle = os.fdopen(read_fd)
    os.set_blocking(read_fd, False)
    print("before")
    with redirect_to_file_descriptor(write_fd):
        print("during1")
        print("from stderr1", file=sys.stderr)
        print("during2")
        print("from stderr2", file=sys.stderr)
        print("from stderr3", file=sys.stderr)
        line = None
        lines = []
        while line is None or len(line) > 0:
            line = read_handle.readline()
            if len(line) > 0:
                lines.append(line)
    print("after")

    assert lines == [
        "during1\n",
        "from stderr1\n",
        "during2\n",
        "from stderr2\n",
        "from stderr3\n",
    ]
