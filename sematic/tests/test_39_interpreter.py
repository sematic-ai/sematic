import sys

import requests  # confirm that third party dependencies were installed

def test_py39():
    assert sys.version_info[0:2] == (3, 9)