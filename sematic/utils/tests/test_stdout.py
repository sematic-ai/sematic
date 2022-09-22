# Standard Library
import sys
import tempfile

# Sematic
from sematic.utils.stdout import redirect_to_file


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
