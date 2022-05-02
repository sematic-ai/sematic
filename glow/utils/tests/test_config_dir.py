# Glow
from glow.utils.config_dir import get_config_dir


def test_get_config_dir():
    assert isinstance(get_config_dir(), str)
    # Making sure this is idempotent
    assert isinstance(get_config_dir(), str)
