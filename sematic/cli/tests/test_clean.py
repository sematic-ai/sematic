# Standard Library
from unittest import mock

# Third-party
from click.testing import CliRunner

# Sematic
from sematic.cli.clean import clean


@mock.patch("sematic.cli.clean.clean_orphaned_resources")
@mock.patch("sematic.cli.clean.clean_orphaned_jobs")
def test_clean(
    mock_clean_orphaned_jobs: mock.MagicMock,
    mock_clean_orphaned_resources: mock.MagicMock,
):

    runner = CliRunner()

    runner.invoke(clean, [])
    mock_clean_orphaned_resources.assert_not_called()
    mock_clean_orphaned_jobs.assert_not_called()

    runner.invoke(clean, ["--orphaned-jobs"])
    mock_clean_orphaned_resources.assert_not_called()
    mock_clean_orphaned_jobs.assert_called()

    mock_clean_orphaned_jobs.reset_mock()
    runner.invoke(clean, ["--orphaned-resources"])
    mock_clean_orphaned_resources.assert_called()
    mock_clean_orphaned_jobs.assert_not_called()

    mock_clean_orphaned_jobs.reset_mock()
    mock_clean_orphaned_resources.reset_mock()
    runner.invoke(clean, ["--orphaned-resources"])
    mock_clean_orphaned_resources.assert_called()
    mock_clean_orphaned_jobs.assert_not_called()
