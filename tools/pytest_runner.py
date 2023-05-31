import os
import sys

import debugpy
import pytest
import sematic.torch_patch

if __name__ == "__main__":
    if os.environ.get("DEBUGPY", None) is not None:
        debugpy.listen(5724)

        # blocks execution until client is attached
        debugpy.wait_for_client()

    pytest_args = []
    pytest_args.extend(sys.argv[1:])

    raise SystemExit(pytest.main(pytest_args))
