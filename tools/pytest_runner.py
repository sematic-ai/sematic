import sys

import pytest

if __name__ == "__main__":
    pytest_args = []
    pytest_args.extend(sys.argv[1:])

    raise SystemExit(pytest.main(pytest_args))
