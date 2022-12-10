# Standard Library
import tempfile
from unittest.mock import PropertyMock, patch

# Sematic
from sematic.config.server_settings import get_active_server_settings


def test_fresh_start():
    with tempfile.TemporaryDirectory() as td:
        with patch(
            "sematic.config.settings.get_config_dir",
            return_value=td,
            new_callable=PropertyMock,
        ):
            assert get_active_server_settings() == {}
