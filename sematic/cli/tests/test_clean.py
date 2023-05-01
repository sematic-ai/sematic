# Standard Library
from unittest import mock

# Third-party
from click.testing import CliRunner

# Sematic
from sematic.cli.clean import clean


@mock.patch("sematic.cli.clean.clean_stale_resolutions")
@mock.patch("sematic.cli.clean.clean_orphaned_runs")
@mock.patch("sematic.cli.clean.clean_orphaned_resources")
@mock.patch("sematic.cli.clean.clean_orphaned_jobs")
def test_clean(
    mock_clean_orphaned_jobs: mock.MagicMock,
    mock_clean_orphaned_resources: mock.MagicMock,
    mock_clean_orphaned_runs: mock.MagicMock,
    mock_clean_stale_resolutions: mock.MagicMock,
):
    def reset():
        mock_clean_orphaned_jobs.reset_mock()
        mock_clean_orphaned_resources.reset_mock()
        mock_clean_orphaned_runs.reset_mock()
        mock_clean_stale_resolutions.reset_mock()

    runner = CliRunner()

    runner.invoke(clean, [])
    mock_clean_orphaned_runs.assert_not_called()
    mock_clean_stale_resolutions.assert_not_called()
    mock_clean_orphaned_resources.assert_not_called()
    mock_clean_orphaned_jobs.assert_not_called()

    runner.invoke(clean, ["--orphaned-jobs"])
    mock_clean_orphaned_runs.assert_not_called()
    mock_clean_stale_resolutions.assert_not_called()
    mock_clean_orphaned_resources.assert_not_called()
    mock_clean_orphaned_jobs.assert_called()

    reset()
    runner.invoke(clean, ["--orphaned-resources"])
    mock_clean_orphaned_runs.assert_not_called()
    mock_clean_stale_resolutions.assert_not_called()
    mock_clean_orphaned_resources.assert_called()
    mock_clean_orphaned_jobs.assert_not_called()

    reset()
    runner.invoke(clean, ["--orphaned-runs"])
    mock_clean_orphaned_runs.assert_called()
    mock_clean_stale_resolutions.assert_not_called()
    mock_clean_orphaned_resources.assert_not_called()
    mock_clean_orphaned_jobs.assert_not_called()

    reset()
    runner.invoke(clean, ["--stale-resolutions", "--orphaned-resources"])
    mock_clean_orphaned_runs.assert_not_called()
    mock_clean_stale_resolutions.assert_called()
    mock_clean_orphaned_resources.assert_called()
    mock_clean_orphaned_jobs.assert_not_called()
