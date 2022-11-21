# Standard Library
from unittest import mock

# Third-party
from click.testing import CliRunner

# Sematic
from sematic.cli.cancel import cancel
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import persisted_run, run, test_db  # noqa: F401


@mock.patch("sematic.cli.cancel.api_client.get_run")
@mock.patch("sematic.cli.cancel.api_client.cancel_resolution")
def test_cancel_abort(
    mock_cancel_resolution: mock.MagicMock,
    mock_get_run: mock.MagicMock,
    persisted_run: Run,  # noqa: F811
):
    mock_get_run.return_value = persisted_run

    runner = CliRunner()

    runner.invoke(cancel, ["abc"], input="n")

    mock_cancel_resolution.assert_not_called()


@mock.patch("sematic.cli.cancel.api_client.get_run")
@mock.patch("sematic.cli.cancel.api_client.cancel_resolution")
def test_cancel_confirm(
    mock_cancel_resolution: mock.MagicMock,
    mock_get_run: mock.MagicMock,
    persisted_run: Run,  # noqa: F811
):
    mock_get_run.return_value = persisted_run

    runner = CliRunner()

    runner.invoke(cancel, ["abc"], input="Y")

    mock_cancel_resolution.assert_called_with(persisted_run.root_id)
