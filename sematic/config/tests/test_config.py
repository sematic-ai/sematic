# Standard Library
from dataclasses import fields, replace

# Third-party
import pytest

# Sematic
from sematic.config.config import Config, _get_db_password


def test_config_string_rep():
    # Not: the values here are not necessarily something that
    # could actually be consgtructed for a real config.
    db_password = "kx%40jj5%2Fg"
    config = Config(
        server_address="126.1.1.2",
        api_version=1,
        port=81,
        db_url=f"postgresql+pg8000://dbuser:{db_password}@pghost10/appdb",
        config_dir="/home/spock/.sematic",
        migrations_dir="/home/spock/migrations",
        base_dir="/base/dir",
        examples_dir="/exqmples/dir",
        project_template_dir="/templates/dir",
        data_dir="/data/dir",
        server_log_to_stdout=True,
        _wsgi_workers_count=2,
    )
    as_str = str(config)
    as_repr = repr(config)
    assert as_str == as_repr

    assert db_password not in as_str
    assert "dbuser" in as_str
    assert "Config(" in as_str
    assert all(f"{field.name}=" in as_str for field in fields(Config))

    db_url = "sqlite:///some/file/dir/db.sqlite3"
    config = replace(config, db_url=db_url)
    as_str = str(config)
    as_repr = repr(config)
    assert as_str == as_repr
    assert db_url in as_str


_DB_URL_PASSOWRD_PAIRS = [
    ("postgresql+pg8000://dbuser@pghost10/appdb", None),
    ("some@random:string@blah", None),
    ("sqlite:///some/file/dir/db.sqlite3", None),
    ("postgresql+pg8000://dbuser:sUpEr$eCr3+@pghost10/appdb", "sUpEr$eCr3+"),
]


@pytest.mark.parametrize("url, expected", _DB_URL_PASSOWRD_PAIRS)
def test_get_db_password(url, expected):
    actual = _get_db_password(url)
    assert actual == expected
