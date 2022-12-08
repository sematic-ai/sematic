# Standard Library
import os
import tempfile
from unittest.mock import PropertyMock, patch

# Third-party
import yaml

# Sematic
from sematic.config.server_settings import get_active_server_settings
from sematic.config.user_settings import UserSettingsVar, set_user_settings


def test_migration():
    with tempfile.TemporaryDirectory() as td:
        with patch(
            "sematic.config.settings.get_config_dir",
            return_value=td,
            new_callable=PropertyMock,
        ):
            set_user_settings(UserSettingsVar.AWS_S3_BUCKET, "foo")
            assert get_active_server_settings() == {}

            with open(os.path.join(td, "server.yaml"), "r") as f:
                server_settings = yaml.load(f, yaml.Loader)

            assert server_settings == {
                "default": {UserSettingsVar.AWS_S3_BUCKET.value: "foo"}
            }


def test_fresh_start():
    with tempfile.TemporaryDirectory() as td:
        with patch(
            "sematic.config.settings.get_config_dir",
            return_value=td,
            new_callable=PropertyMock,
        ):
            assert get_active_server_settings() == {}
