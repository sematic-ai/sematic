# Standard Library
import os

# Third-party
import pytest

# Sematic
import sematic.user_settings as user_settings
from sematic.api.tests.fixtures import mock_settings_file  # noqa: F401
from sematic.tests.fixtures import environment_variables
from sematic.user_settings import (
    MissingSettingsError,
    SettingsVar,
    UserSettings,
    _load_settings,
    delete_profile,
    delete_user_settings,
    get_active_user_settings,
    get_default_settings,
    get_profiles,
    get_user_settings,
    set_active_profile,
    set_user_settings,
)

_TEST_FILE = "sematic/tests/data/test_settings.yaml"
_TEST_DEPRECATED_FILE = "sematic/tests/data/test_version_0_settings.yaml"


@pytest.mark.parametrize("mock_settings_file", [_TEST_DEPRECATED_FILE], indirect=True)
def test_settings_migration(mock_settings_file):  # noqa: F811
    assert get_active_user_settings() == {SettingsVar.AWS_S3_BUCKET: "sematic-dev"}
    assert user_settings._settings == UserSettings(
        active_profile="dev",
        profiles={"dev": {SettingsVar.AWS_S3_BUCKET.value: "sematic-dev"}},
    )

    settings_file_path = user_settings._get_settings_file()
    # the archive will be created in the bazel workspace, not in the user home
    assert os.path.exists(f"{settings_file_path}.v0")


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_get_active_user_settings(mock_settings_file):  # noqa: F811
    assert get_active_user_settings() == {SettingsVar.SNOWFLAKE_USER: "foobar"}


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_get_active_user_settings_env_override(mock_settings_file):  # noqa: F811

    with environment_variables(
        {
            str(SettingsVar.SNOWFLAKE_USER.value): "baz",
            str(SettingsVar.KUBERNETES_NAMESPACE.value): "quux",
            "unrelated": "unrelated",
        }
    ):
        assert get_active_user_settings() == {
            SettingsVar.SNOWFLAKE_USER: "baz",
            SettingsVar.KUBERNETES_NAMESPACE: "quux",
        }


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_get_active_user_empty_settings(mock_settings_file):  # noqa: F811
    assert get_active_user_settings() == {}


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_get_active_user_empty_settings_env_override(mock_settings_file):  # noqa: F811

    with environment_variables(
        {
            str(SettingsVar.SNOWFLAKE_USER.value): "baz",
            str(SettingsVar.KUBERNETES_NAMESPACE.value): "quux",
            "unrelated": "unrelated",
        }
    ):
        assert get_active_user_settings() == {
            SettingsVar.SNOWFLAKE_USER: "baz",
            SettingsVar.KUBERNETES_NAMESPACE: "quux",
        }


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_get_settings(mock_settings_file):  # noqa: F811
    assert get_user_settings(SettingsVar.SNOWFLAKE_USER) == "foobar"


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_get_settings_env_override(mock_settings_file):  # noqa: F811

    assert get_user_settings(SettingsVar.SNOWFLAKE_USER) == "foobar"

    with environment_variables({str(SettingsVar.SNOWFLAKE_USER.value): "quux"}):
        assert get_user_settings(SettingsVar.SNOWFLAKE_USER) == "foobar"
        user_settings._settings = None
        assert get_user_settings(SettingsVar.SNOWFLAKE_USER) == "quux"


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_get_missing_settings_raises(mock_settings_file):  # noqa: F811
    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_get_missing_settings_env_override(mock_settings_file):  # noqa: F811

    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

    with environment_variables({str(SettingsVar.SEMATIC_API_ADDRESS.value): "quux"}):
        with pytest.raises(MissingSettingsError):
            get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

        user_settings._settings = None
        assert get_user_settings(SettingsVar.SEMATIC_API_ADDRESS) == "quux"


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_set_settings(mock_settings_file):  # noqa: F811

    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

    set_user_settings(SettingsVar.SEMATIC_API_ADDRESS, "baz")
    assert get_user_settings(SettingsVar.SEMATIC_API_ADDRESS) == "baz"
    user_settings._settings = None
    assert get_user_settings(SettingsVar.SEMATIC_API_ADDRESS) == "baz"


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_set_settings_env_override(mock_settings_file):  # noqa: F811

    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

    set_user_settings(SettingsVar.SEMATIC_API_ADDRESS, "baz")

    with environment_variables({str(SettingsVar.SEMATIC_API_ADDRESS.value): "quux"}):
        assert get_user_settings(SettingsVar.SEMATIC_API_ADDRESS) == "baz"
        user_settings._settings = None
        assert get_user_settings(SettingsVar.SEMATIC_API_ADDRESS) == "quux"


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_overwrite_settings(mock_settings_file):  # noqa: F811

    assert get_user_settings(SettingsVar.SNOWFLAKE_USER) == "foobar"
    set_user_settings(SettingsVar.SNOWFLAKE_USER, "baz")
    assert get_user_settings(SettingsVar.SNOWFLAKE_USER) == "baz"
    user_settings._settings = None
    assert get_user_settings(SettingsVar.SNOWFLAKE_USER) == "baz"


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_delete_settings(mock_settings_file):  # noqa: F811

    delete_user_settings(SettingsVar.SNOWFLAKE_USER)
    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SNOWFLAKE_USER)

    user_settings._settings = None
    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SNOWFLAKE_USER)


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_delete_missing_settings_raises(mock_settings_file):  # noqa: F811
    with pytest.raises(ValueError, match=r".* is not present in the active profile!"):
        delete_user_settings(SettingsVar.SEMATIC_API_ADDRESS)


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_set_and_delete_settings(mock_settings_file):  # noqa: F811

    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

    set_user_settings(SettingsVar.SEMATIC_API_ADDRESS, "baz")
    delete_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_delete_and_set_settings(mock_settings_file):  # noqa: F811

    delete_user_settings(SettingsVar.SNOWFLAKE_USER)
    set_user_settings(SettingsVar.SNOWFLAKE_USER, "baz")

    assert get_user_settings(SettingsVar.SNOWFLAKE_USER) == "baz"
    user_settings._settings = None
    assert get_user_settings(SettingsVar.SNOWFLAKE_USER) == "baz"


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_get_empty_settings_defaults(mock_settings_file):  # noqa: F811
    assert _load_settings() == get_default_settings()


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_get_empty_missing_settings_raises(mock_settings_file):  # noqa: F811
    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_set_empty_settings(mock_settings_file):  # noqa: F811

    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

    set_user_settings(SettingsVar.SEMATIC_API_ADDRESS, "baz")
    assert get_user_settings(SettingsVar.SEMATIC_API_ADDRESS) == "baz"
    user_settings._settings = None
    assert get_user_settings(SettingsVar.SEMATIC_API_ADDRESS) == "baz"


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_set_empty_settings_env_override(mock_settings_file):  # noqa: F811

    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)
    set_user_settings(SettingsVar.SEMATIC_API_ADDRESS, "baz")

    with environment_variables({str(SettingsVar.SEMATIC_API_ADDRESS.value): "quux"}):
        assert get_user_settings(SettingsVar.SEMATIC_API_ADDRESS) == "baz"
        user_settings._settings = None
        assert get_user_settings(SettingsVar.SEMATIC_API_ADDRESS) == "quux"


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_delete_missing_empty_settings_raises(mock_settings_file):  # noqa: F811
    with pytest.raises(ValueError, match=r".* is not present in the active profile!"):
        delete_user_settings(SettingsVar.SEMATIC_API_ADDRESS)


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_get_missing_empty_settings_env_override(mock_settings_file):  # noqa: F811

    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

    with environment_variables({str(SettingsVar.SEMATIC_API_ADDRESS.value): "quux"}):
        with pytest.raises(MissingSettingsError):
            get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

        user_settings._settings = None
        assert get_user_settings(SettingsVar.SEMATIC_API_ADDRESS) == "quux"


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_set_and_delete_empty_settings(mock_settings_file):  # noqa: F811

    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

    set_user_settings(SettingsVar.SEMATIC_API_ADDRESS, "baz")
    delete_user_settings(SettingsVar.SEMATIC_API_ADDRESS)

    with pytest.raises(MissingSettingsError):
        get_user_settings(SettingsVar.SEMATIC_API_ADDRESS)


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_get_profiles(mock_settings_file):  # noqa: F811

    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "default"
    assert inactive_profiles == ["dev1", "dev2"]
    assert get_active_user_settings() == {SettingsVar.SNOWFLAKE_USER: "foobar"}


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_switch_profile(mock_settings_file):  # noqa: F811

    set_active_profile("dev2")
    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "dev2"
    assert inactive_profiles == ["default", "dev1"]
    assert get_active_user_settings() == {
        SettingsVar.AWS_S3_BUCKET: "sematic-dev",
        SettingsVar.KUBERNETES_NAMESPACE: "dev2",
    }


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_switch_profile_switch_back(mock_settings_file):  # noqa: F811

    set_active_profile("dev2")
    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "dev2"
    assert inactive_profiles == ["default", "dev1"]
    assert get_active_user_settings() == {
        SettingsVar.AWS_S3_BUCKET: "sematic-dev",
        SettingsVar.KUBERNETES_NAMESPACE: "dev2",
    }

    set_active_profile("default")
    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "default"
    assert inactive_profiles == ["dev1", "dev2"]


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_create_profile(mock_settings_file):  # noqa: F811

    set_active_profile("test")
    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "test"
    assert inactive_profiles == ["default", "dev1", "dev2"]
    assert get_active_user_settings() == {}


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_create_profile_switch_back(mock_settings_file):  # noqa: F811

    set_active_profile("test")
    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "test"
    assert inactive_profiles == ["default", "dev1", "dev2"]
    assert get_active_user_settings() == {}

    set_active_profile("default")
    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "default"
    assert inactive_profiles == ["dev1", "dev2", "test"]
    assert get_active_user_settings() == {SettingsVar.SNOWFLAKE_USER: "foobar"}


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_create_illegal_profile_raises(mock_settings_file):  # noqa: F811

    with pytest.raises(ValueError, match="The profile name cannot be empty!"):
        set_active_profile("")

    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "default"
    assert inactive_profiles == ["dev1", "dev2"]
    assert get_active_user_settings() == {SettingsVar.SNOWFLAKE_USER: "foobar"}


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_delete_profile(mock_settings_file):  # noqa: F811

    delete_profile("dev1")
    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "default"
    assert inactive_profiles == ["dev2"]
    assert get_active_user_settings() == {SettingsVar.SNOWFLAKE_USER: "foobar"}


@pytest.mark.parametrize("mock_settings_file", [_TEST_FILE], indirect=True)
def test_delete_active_profile_raises(mock_settings_file):  # noqa: F811

    with pytest.raises(
        ValueError,
        match="Cannot delete the active profile! Switch to another profile first!",
    ):
        delete_profile("default")

    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "default"
    assert inactive_profiles == ["dev1", "dev2"]
    assert get_active_user_settings() == {SettingsVar.SNOWFLAKE_USER: "foobar"}


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_get_profiles_empty_settings(mock_settings_file):  # noqa: F811

    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "default"
    assert inactive_profiles == []


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_create_profile_empty_settings(mock_settings_file):  # noqa: F811

    set_active_profile("test")
    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "test"
    assert inactive_profiles == ["default"]


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_create_profile_switch_back_empty_settings(mock_settings_file):  # noqa: F811

    set_active_profile("test")
    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "test"
    assert inactive_profiles == ["default"]
    assert get_active_user_settings() == {}

    set_active_profile("default")
    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "default"
    assert inactive_profiles == ["test"]
    assert get_active_user_settings() == {}


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_create_illegal_profile_empty_settings_raises(mock_settings_file):  # noqa: F811

    with pytest.raises(ValueError, match="The profile name cannot be empty!"):
        set_active_profile("")
    active_profile, inactive_profiles = get_profiles()

    assert active_profile == "default"
    assert inactive_profiles == []
    assert get_active_user_settings() == {}


@pytest.mark.parametrize("mock_settings_file", [None], indirect=True)
def test_delete_active_profile_empty_settings_raises(mock_settings_file):  # noqa: F811

    with pytest.raises(
        ValueError,
        match="Cannot delete the active profile! Switch to another profile first!",
    ):
        delete_profile("default")

    active_profile, inactive_profiles = get_profiles()
    assert active_profile == "default"
    assert inactive_profiles == []
    assert get_active_user_settings() == {}
