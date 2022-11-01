# Standard Library
import tempfile
from dataclasses import asdict

# Third-party
import pytest

# Sematic
from sematic.config import Config, get_config, set_config
from sematic.db.tests.fixtures import test_db  # noqa: F401


@pytest.fixture
def test_config(test_db):  # noqa: F811
    current_config = get_config()
    new_config = Config(**asdict(current_config))
    new_config.port = 5010
    new_config.config_dir = tempfile.mkdtemp()
    set_config(new_config)
    try:
        yield
    finally:
        set_config(current_config)


def test_start(test_config):
    """
    runner = CliRunner()
    assert not server_is_running()
    result = runner.invoke(main.start)
    assert result.exit_code == 0
    process = subprocess.run("ps | grep sematic", shell=True, capture_output=True)
    assert server_is_running()

    process = subprocess.run(
        "netstat -na | grep {}".format(get_config().port),
        shell=True,
        capture_output=True,
    )

    assert len(process.stdout.decode()) == 1

    result = runner.invoke(main.stop)
    assert result.exit_code == 0

    assert not server_is_running()

    process = subprocess.run(
        "netstat -na | grep {}".format(get_config().port),
        shell=True,
        capture_output=True,
    )
    assert len(process.stdout.decode()) == 0
    """
    pass
