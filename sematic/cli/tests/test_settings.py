# Standard Library
from unittest.mock import patch

# Third-party
from click.testing import CliRunner

# Sematic
from sematic.cli.settings import set_settings_cli
from sematic.config.user_settings import UserSettings, UserSettingsVar
from sematic.plugins.storage.s3_storage import S3Storage, S3StorageSettingsVar


@patch("sematic.cli.settings.set_plugin_setting")
def test_set_settings_cli(mock_set_plugin_setting):
    runner = CliRunner()

    with runner.isolated_filesystem():
        fake_address = "foo.com"
        result = runner.invoke(
            set_settings_cli, [UserSettingsVar.SEMATIC_API_ADDRESS.value, fake_address]
        )
        assert result.exception is None

        mock_set_plugin_setting.assert_called_with(
            UserSettings,
            UserSettingsVar.SEMATIC_API_ADDRESS,
            fake_address,
        )

        fake_bucket = "fake_bucket"
        result = runner.invoke(
            set_settings_cli,
            [
                S3StorageSettingsVar.AWS_S3_BUCKET.value,
                fake_bucket,
                "-p",
                f"{S3Storage.__module__}.{S3Storage.__name__}",
            ],
        )
        assert result.exception is None

        mock_set_plugin_setting.assert_called_with(
            S3Storage,
            S3StorageSettingsVar.AWS_S3_BUCKET,
            fake_bucket,
        )
