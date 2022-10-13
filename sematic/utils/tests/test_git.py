# Standard Library
import sys


def test_import():
    """
    Tests that importing `sematic.db.git` does not automatically import the git-python
    `git` module directly.
    """
    assert "git" not in sys.modules.keys()
    # Sematic
    import sematic.utils.git  # noqa: F401

    assert "git" not in sys.modules.keys()
    # Sematic
    from sematic.utils.git import get_git_info

    assert "git" not in sys.modules.keys()
    get_git_info(get_git_info)
    assert "git" in sys.modules.keys()
