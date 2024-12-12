# Standard Library
import logging
import sys


def test_import():
    """
    Tests that importing `sematic.db.git` does not automatically import the git-python
    `git` module directly.
    """
    if "git" in sys.modules.keys():
        logging.warning("This test should be run in its own interpreter")
        return
    # Sematic
    import sematic.utils.git  # noqa: F401

    assert "git" not in sys.modules.keys()
    # Sematic
    from sematic.utils.git import get_git_info

    assert "git" not in sys.modules.keys()
    get_git_info(get_git_info)
    assert "git" in sys.modules.keys()
