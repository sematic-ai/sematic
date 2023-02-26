# Standard Library
import tempfile
from unittest import mock

# Third-party
import pytest
from click.testing import CliRunner

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import mock_storage  # noqa: F401
from sematic.cli.logs import dump_log_storage, logs
from sematic.db.models.resolution import ResolutionStatus
from sematic.db.queries import save_resolution, save_run
from sematic.db.tests.fixtures import make_resolution, make_run, test_db  # noqa: F401
from sematic.log_reader import LogLineResult, log_prefix
from sematic.scheduling.external_job import ExternalJob, JobType


@pytest.fixture
def mock_api_client():
    with mock.patch("sematic.cli.logs.api_client") as mock_api_client:
        with mock.patch(
            "sematic.log_reader.api_client", new_callable=lambda: mock_api_client
        ):
            with mock.patch("sematic.cli.logs.ObjectSource") as mock_source:
                mock_source.API = mock_api_client
                yield mock_api_client


@pytest.fixture
def mock_load_log_lines():
    with mock.patch("sematic.cli.logs.load_log_lines") as mock_loader:
        yield mock_loader


MOCK_LINES = [f"Hello {i}" for i in range(1000)]


def fill_log_dir(mock_storage, text_lines, prefix):  # noqa: F811
    break_at_line = 52
    lines_part_1 = text_lines[:break_at_line]
    lines_part_2 = text_lines[break_at_line:]

    log_file_contents_part_1 = bytes("\n".join(lines_part_1), encoding="utf8")
    key_part_1 = f"{prefix}12345.log"
    mock_storage.set(key_part_1, log_file_contents_part_1)

    log_file_contents_part_2 = bytes("\n".join(lines_part_2), encoding="utf8")
    key_part_2 = f"{prefix}12346.log"
    mock_storage.set(key_part_2, log_file_contents_part_2)
    return prefix


def test_logs(test_db, mock_storage, mock_api_client):  # noqa: F811
    run = make_run(future_state=FutureState.RESOLVED)
    run.external_jobs = [ExternalJob(JobType.driver, 0, external_job_id="abc")]
    resolution = make_resolution(root_id=run.id, status=ResolutionStatus.COMPLETE)
    save_run(run)
    save_resolution(resolution)
    runner = CliRunner()
    fill_log_dir(mock_storage, MOCK_LINES, log_prefix(run.id, JobType.worker))
    mock_api_client.get_run = lambda x: run
    mock_api_client.get_resolution = lambda x: resolution

    result = runner.invoke(logs, [run.id])
    assert result.exit_code == 0
    assert list(result.output.split("\n"))[:-1] == MOCK_LINES


def test_follow_logs(
    test_db, mock_storage, mock_api_client, mock_load_log_lines  # noqa: F811
):
    run = make_run(future_state=FutureState.RESOLVED)
    run.external_jobs = [ExternalJob(JobType.driver, 0, external_job_id="abc")]
    resolution = make_resolution(root_id=run.id, status=ResolutionStatus.COMPLETE)
    save_run(run)
    save_resolution(resolution)
    runner = CliRunner()
    mock_api_client.get_run = lambda x: run
    mock_api_client.get_resolution = lambda x: resolution
    early_lines = ["out a", "out b", "out c"]
    late_lines = ["out d", "out e"]

    live_log_returns = [
        LogLineResult(
            more_before=False,
            more_after=True,
            lines=early_lines,
            continuation_cursor="abc",
            log_info_message=None,
        ),
        LogLineResult(
            more_before=False,
            more_after=True,
            lines=[],  # simulate situation where more WILL be produced but isn't yet
            continuation_cursor="abc",
            log_info_message=None,
        ),
        LogLineResult(
            more_before=False,
            more_after=False,
            lines=late_lines,
            continuation_cursor=None,
            log_info_message=None,
        ),
    ]
    mock_returns = []

    def fake_return_logs(*args, **kwargs):
        result = mock_returns[0]
        mock_returns.remove(result)
        return result

    mock_load_log_lines.side_effect = fake_return_logs

    mock_returns.extend(live_log_returns)
    result = runner.invoke(logs, [run.id])
    assert result.exit_code == 0
    # As soon as it got to the end of the lines that had been produced
    # "so far" it should have stopped looking for more.
    assert list(result.output.split("\n"))[:-1] == early_lines

    mock_returns.clear()
    mock_returns.extend(live_log_returns)
    result = runner.invoke(logs, [run.id, "-f"])
    assert result.exit_code == 0
    assert list(result.output.split("\n"))[:-1] == early_lines + late_lines

    mock_returns.clear()
    mock_returns.extend(live_log_returns)
    result = runner.invoke(logs, [run.id, "--follow"])
    assert result.exit_code == 0
    assert list(result.output.split("\n"))[:-1] == early_lines + late_lines


def test_empty_logs(test_db, mock_storage, mock_api_client):  # noqa: F811
    run = make_run(future_state=FutureState.RESOLVED)
    run.external_jobs = [ExternalJob(JobType.driver, 0, external_job_id="abc")]
    resolution = make_resolution(root_id=run.id, status=ResolutionStatus.COMPLETE)
    save_run(run)
    save_resolution(resolution)
    runner = CliRunner()
    mock_api_client.get_run = lambda x: run
    mock_api_client.get_resolution = lambda x: resolution

    result = runner.invoke(logs, [run.id])
    assert result.exit_code == 1
    assert list(result.output.split("\n"))[:-1] == ["No log files found"]


def test_dump_log_dir(mock_storage):  # noqa: F811
    with tempfile.TemporaryDirectory() as temp_dir:
        fill_log_dir(mock_storage, MOCK_LINES, f"{temp_dir}/")
        runner = CliRunner()
        result = runner.invoke(dump_log_storage, [temp_dir])
        assert result.exit_code == 0
        assert list(result.output.split("\n"))[:-1] == MOCK_LINES


def test_dump_empty_log_dir(mock_storage):  # noqa: F811
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = CliRunner()
        result = runner.invoke(dump_log_storage, [temp_dir])
        assert result.exit_code == 1
        assert list(result.output.split("\n"))[:-1] == [
            f"No logs found in storage at '{temp_dir}/'"
        ]
