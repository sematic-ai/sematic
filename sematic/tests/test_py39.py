import sys
import requests

def test_py39():
    assert sys.version_info[0:2] == (3, 9)