# Standard Library
import logging
import os
import sys
import tempfile
from typing import Any, Optional
from unittest import mock

# Third-party
import pytest

# Sematic
import docker
from sematic.plugins.building import docker_builder
from sematic.tests.utils import assert_logs_captured

# this is the relative path inside the bazel sandbox where the data files will be copied
# they are repo-relative instead of build file-relative
_RESOURCE_PATH = os.path.join("sematic", "plugins", "building", "tests", "fixtures")
_LAUNCH_SCRIPT = os.path.join(_RESOURCE_PATH, "good_launch_script.py")
_IMAGE_SHA = "sha256:bea3926876a3024c33fe08e0a6b2c0377a7eb600d7b3061a3f3f39d711152e3c"
_BASE_IMAGE_URI = f"sematicai/sematic-worker-base:latest@{_IMAGE_SHA}"
_LOCAL_IMAGE_NAME = "fixtures:default_my_tag_suffix"
_LOCAL_IMAGE_URI = f"{_LOCAL_IMAGE_NAME}@{_IMAGE_SHA}"
_REMOTE_IMAGE_NAME = "my_registry.com/my_repository:default_my_tag_suffix"
_REMOTE_IMAGE_URI = f"{_REMOTE_IMAGE_NAME}@{_IMAGE_SHA}"

_PUSH_CONFIG = docker_builder.ImagePushConfig(
    registry="my_registry.com", repository="my_repository", tag_suffix="my_tag_suffix"
)


@pytest.fixture(scope="function")
def mock_image() -> mock.Mock:
    mock_image = mock.Mock(docker.models.images.Image)  # type: ignore
    mock_image.id = _IMAGE_SHA
    mock_image.attrs = {"RepoTags": [_LOCAL_IMAGE_NAME], "RepoDigests": []}

    def mock_reload():
        mock_image.attrs = {
            "RepoTags": [_REMOTE_IMAGE_NAME, _LOCAL_IMAGE_NAME],
            "RepoDigests": [_REMOTE_IMAGE_URI],
        }

    mock_image.reload.side_effect = mock_reload
    mock_image.tag.return_value = True

    return mock_image


@pytest.fixture(scope="function")
def mock_docker_client(mock_image: mock.Mock) -> mock.Mock:
    mock_docker_client = mock.Mock(docker.DockerClient)  # type: ignore
    mock_docker_api = mock.Mock(docker.APIClient)  # type: ignore
    mock_docker_api.base_url = "my_docker_server"
    mock_docker_client.api = mock_docker_api
    mock_docker_client.images.push.return_value = [
        {"id": 1, "status": "Preparing"},
        {"id": 2, "status": "Layer already exists"},
    ]
    mock_docker_client.api.build.return_value = [
        {"stream": "Step 1/14 : FROM sematicai/sematic-worker-base:latest"},
        {"stream": ""},
        {"stream": "---> Using cache"},
    ]
    mock_docker_client.images.get.return_value = mock_image
    return mock_docker_client


@mock.patch("sematic.plugins.building.docker_builder._push_image")
@mock.patch("sematic.plugins.building.docker_builder._make_docker_client")
def test_build_base_uri_happy(
    mock_make_docker_client: mock.MagicMock,
    mock_push_image: mock.MagicMock,
    mock_docker_client: mock.Mock,
    mock_image: mock.Mock,
):
    expected_local_uri = docker_builder.ImageURI.from_uri(_LOCAL_IMAGE_URI)
    mock_make_docker_client.return_value = mock_docker_client
    mock_push_image.return_value = docker_builder.ImageURI.from_uri(_REMOTE_IMAGE_URI)

    actual_image_uri = docker_builder._build(target=_LAUNCH_SCRIPT)

    assert repr(actual_image_uri) == _REMOTE_IMAGE_URI
    mock_push_image.assert_called_once_with(
        image=mock_image,
        image_uri=expected_local_uri,
        push_config=mock.ANY,
        docker_client=mock_docker_client,
    )


@mock.patch("sematic.plugins.building.docker_builder._push_image")
@mock.patch("sematic.plugins.building.docker_builder._make_docker_client")
def test_build_image_script_happy(
    mock_make_docker_client: mock.MagicMock,
    mock_push_image: mock.MagicMock,
    mock_docker_client: mock.Mock,
    mock_image: mock.Mock,
):
    # determine loading the image_script build config
    target = os.path.join(_RESOURCE_PATH, "good_minimal.py")
    expected_local_uri = docker_builder.ImageURI.from_uri(_LOCAL_IMAGE_URI)
    mock_make_docker_client.return_value = mock_docker_client
    mock_push_image.return_value = docker_builder.ImageURI.from_uri(_REMOTE_IMAGE_URI)

    actual_image_uri = docker_builder._build(target=target)

    assert repr(actual_image_uri) == _REMOTE_IMAGE_URI
    mock_push_image.assert_called_once_with(
        image=mock_image,
        image_uri=expected_local_uri,
        push_config=mock.ANY,
        docker_client=mock_docker_client,
    )


@mock.patch("sematic.plugins.building.docker_builder._make_docker_client")
def test_build_error(
    mock_make_docker_client: mock.MagicMock,
    mock_docker_client: mock.Mock,
    mock_image: mock.Mock,
    caplog: Any,
):
    mock_make_docker_client.return_value = mock_docker_client
    mock_docker_client.api.build.return_value = [
        {"stream": "Step 1/14 : FROM sematicai/sematic-worker-base:latest"},
        {"stream": ""},
        {"error": "didn't work", "errorDetail": "it hit the fan"},
    ]

    with caplog.at_level(logging.ERROR):
        with pytest.raises(
            docker_builder.BuildError, match="Unable to build image .*: didn't work"
        ):
            docker_builder._build(target=_LAUNCH_SCRIPT)

        assert_logs_captured(caplog, "Image build error details: 'it hit the fan'")


@mock.patch("sematic.plugins.building.docker_builder._execute_build_script")
@mock.patch("sematic.plugins.building.docker_builder._build_image_from_base")
def test_build_image_base_uri(
    mock_build_image_from_base: mock.MagicMock,
    mock_execute_build_script: mock.MagicMock,
    mock_docker_client: mock.Mock,
    mock_image: mock.Mock,
):
    base_uri = docker_builder.ImageURI.from_uri(_BASE_IMAGE_URI)
    local_uri = docker_builder.ImageURI.from_uri(_LOCAL_IMAGE_URI)

    mock_build_config = mock.Mock(docker_builder.BuildConfig)
    mock_build_config.base_uri = base_uri
    mock_build_config.image_script = None
    mock_build_image_from_base.return_value = mock_image, local_uri

    actual_image, actual_uri = docker_builder._build_image(
        target=_LAUNCH_SCRIPT,
        build_config=mock_build_config,
        docker_client=mock_docker_client,
    )

    assert actual_image == mock_image
    assert actual_uri == local_uri
    mock_execute_build_script.assert_not_called()
    mock_build_image_from_base.assert_called_once_with(
        target=_LAUNCH_SCRIPT,
        effective_base_uri=base_uri,
        build_config=mock_build_config,
        docker_client=mock_docker_client,
    )


@mock.patch("sematic.plugins.building.docker_builder._build_image_from_base")
def test_build_image_build_script(
    mock_build_image_from_base: mock.MagicMock,
    mock_docker_client: mock.Mock,
    mock_image: mock.Mock,
):
    image_script = os.path.join(_RESOURCE_PATH, "good_image_script.sh")
    base_uri = docker_builder.ImageURI.from_uri(_BASE_IMAGE_URI)
    local_uri = docker_builder.ImageURI.from_uri(_LOCAL_IMAGE_URI)

    mock_build_config = mock.Mock(docker_builder.BuildConfig)
    mock_build_config.base_uri = None
    mock_build_config.image_script = image_script
    mock_build_image_from_base.return_value = mock_image, local_uri

    actual_image, actual_uri = docker_builder._build_image(
        target=_LAUNCH_SCRIPT,
        build_config=mock_build_config,
        docker_client=mock_docker_client,
    )

    assert actual_image == mock_image
    assert actual_uri == local_uri
    mock_build_image_from_base.assert_called_once_with(
        target=_LAUNCH_SCRIPT,
        effective_base_uri=base_uri,
        build_config=mock_build_config,
        docker_client=mock_docker_client,
    )


def test_launch_happy():
    image_uri = docker_builder.ImageURI.from_uri(_BASE_IMAGE_URI)

    with tempfile.NamedTemporaryFile(delete=True) as f:
        orig_argv = sys.argv.copy()
        try:
            # the test script we use is instrumented to write the image uri it sees in its
            # env vars to the file with named passed in the first argument
            # this way we test both argument passing to the script, and image uri passing
            # to the runner
            sys.argv = ["/dummy.py", f.name]
            docker_builder._launch(target=_LAUNCH_SCRIPT, image_uri=image_uri)
        finally:
            sys.argv = orig_argv

        with open(f.name, "rt") as g:
            actual_image_uri = g.read()

    assert actual_image_uri == _BASE_IMAGE_URI


def test_launch_error():
    target = os.path.join(_RESOURCE_PATH, "bad_launch_script.py")
    image_uri = docker_builder.ImageURI.from_uri(_BASE_IMAGE_URI)

    # we go through the same motions as for the happy path, because we are honourable
    with tempfile.NamedTemporaryFile(delete=True) as f:
        orig_argv = sys.argv.copy()
        try:
            sys.argv = ["/dummy.py", f.name]
            with pytest.raises(SystemExit, match="42"):
                docker_builder._launch(target=target, image_uri=image_uri)
        finally:
            sys.argv = orig_argv


def test_get_build_config_full_base_uri_happy():
    actual_config = docker_builder._get_build_config(_LAUNCH_SCRIPT)

    assert actual_config is not None
    assert actual_config.version == docker_builder.BUILD_SCHEMA_VERSION
    assert actual_config.image_script is None
    assert actual_config.base_uri is not None
    assert actual_config.base_uri.repository == "sematicai/sematic-worker-base"
    assert actual_config.base_uri.tag == "latest"
    assert actual_config.base_uri.digest == _IMAGE_SHA
    assert actual_config.build is not None
    assert actual_config.build.platform == "linux/amd64"
    assert actual_config.build.requirements == "requirements.txt"
    assert actual_config.build.data == ["**.txt"]
    assert actual_config.build.src == ["**.py"]
    assert actual_config.push is not None
    assert actual_config.push.registry == "my_registry.com"
    assert actual_config.push.repository == "my_repository"
    assert actual_config.push.tag_suffix == "my_tag_suffix"
    assert actual_config.docker.base_url == "unix://var/run/docker.sock"
    assert actual_config.docker.credstore_env == {
        "DOCKER_TLS_VERIFY": "/home/trudy/legit.cer"
    }


def test_get_build_config_minimal_image_script_happy():
    target = os.path.join(_RESOURCE_PATH, "good_minimal.py")
    expected_image_script = os.path.join(_RESOURCE_PATH, "good_image_script.sh")
    actual_config = docker_builder._get_build_config(target)

    assert actual_config is not None
    assert actual_config.version == docker_builder.BUILD_SCHEMA_VERSION
    assert actual_config.image_script == expected_image_script
    assert actual_config.base_uri is None
    assert actual_config.build is None
    assert actual_config.push is None


@pytest.mark.parametrize(
    "config_file,match",
    [
        ("bad_version.yaml", ".*Unsupported build schema version.*"),
        ("no_image.yaml", "Exactly one of `image_script` and `base_uri`.*"),
        ("two_images.yaml", "Exactly one of `image_script` and `base_uri`.*"),
        ("malformed_uri.yaml", ".*does not conform to the required.*"),
        ("malformed_push1.yaml", ".*`registry` and `repository` must be non-empty.*"),
        (
            "malformed_push2.yaml",
            ".*missing 1 required positional argument: 'repository'",
        ),
    ],
)
def test_get_build_config_errors(config_file: str, match: str):
    config_file = os.path.join(_RESOURCE_PATH, config_file)
    with pytest.raises(docker_builder.BuildConfigurationError, match=match):
        docker_builder._get_build_config(config_file)


@mock.patch("docker.api.client.APIClient._retrieve_server_version")
def test_make_docker_client_no_config(mock_retrieve_server_version: mock.MagicMock):
    mock_retrieve_server_version.return_value = "1.30"

    docker_client = docker_builder._make_docker_client(docker_config=None)

    # the rest of the values depend on the specific version of the docker library,
    # or are pushed down to implementation-specific components,
    # so it doesn't make sense to assert on them
    assert docker_client.api.base_url == "http+docker://localhost"
    assert docker_client.api.credstore_env is None


@mock.patch("docker.api.client.APIClient._retrieve_server_version")
def test_make_docker_client_config(mock_retrieve_server_version: mock.MagicMock):
    mock_retrieve_server_version.return_value = "1.30"

    expected_base_url = "unix://var/run/docker.sock"
    expected_credstore_env = {"DOCKER_TLS_VERIFY": "/home/trudy/legit.cer"}
    docker_config = docker_builder.DockerClientConfig(
        base_url=expected_base_url, credstore_env=expected_credstore_env
    )

    docker_client = docker_builder._make_docker_client(docker_config=docker_config)

    # the rest of the values depend on the specific version of the docker library,
    # or are pushed down to implementation-specific components,
    # so it doesn't make sense to assert on them
    assert docker_client.api.base_url == "http+docker://localhost"
    assert docker_client.api.credstore_env == expected_credstore_env


@mock.patch("docker.api.client.APIClient._retrieve_server_version")
def test_make_docker_client_error(mock_retrieve_server_version: mock.MagicMock):
    test_error = docker.errors.DockerException("test")  # type: ignore
    mock_retrieve_server_version.side_effect = test_error

    expected_base_url = "unix://var/run/docker.sock"
    expected_credstore_env = {"DOCKER_TLS_VERIFY": "/home/trudy/legit.cer"}
    docker_config = docker_builder.DockerClientConfig(
        base_url=expected_base_url, credstore_env=expected_credstore_env
    )

    with pytest.raises(
        docker_builder.BuildError, match="Unable to instantiate Docker client: test"
    ):
        docker_builder._make_docker_client(docker_config=docker_config)


@pytest.mark.parametrize(
    "source_build_config,target,expected_dockerfile",
    [
        (None, None, "docker/Dockerfile.basic"),
        (
            None,
            os.path.join(_RESOURCE_PATH, "good_launch_script.py"),
            "docker/Dockerfile.target",
        ),
        (
            docker_builder.SourceBuildConfig(
                platform=None, requirements="requirements.txt", data=None, src=None
            ),
            os.path.join(_RESOURCE_PATH, "good_launch_script.py"),
            "docker/Dockerfile.requirements",
        ),
        (
            docker_builder.SourceBuildConfig(
                platform=None,
                requirements=None,
                # check globbing
                data=[os.path.join(_RESOURCE_PATH, "**/Dockerfile.*")],
                src=None,
            ),
            os.path.join(_RESOURCE_PATH, "good_launch_script.py"),
            "docker/Dockerfile.data",
        ),
        (
            docker_builder.SourceBuildConfig(
                platform=None,
                requirements=None,
                data=None,
                # intentionally leave out the target to check it is not added
                src=[os.path.join(_RESOURCE_PATH, "bad_launch_script.py")],
            ),
            os.path.join(_RESOURCE_PATH, "good_launch_script.py"),
            "docker/Dockerfile.src",
        ),
        (
            docker_builder.SourceBuildConfig(
                platform=None,
                requirements="requirements.txt",
                data=[
                    os.path.join(_RESOURCE_PATH, "docker"),
                    os.path.join(_RESOURCE_PATH, "*.sh"),
                ],
                # check the target is not duplicated
                # this actually results in an unexpected __init__.py file being included
                # bazel is perhaps responsible for creating it
                src=[os.path.join(_RESOURCE_PATH, "*.py")],
            ),
            os.path.join(_RESOURCE_PATH, "good_launch_script.py"),
            "docker/Dockerfile.full",
        ),
    ],
)
def test_generate_dockerfile_contents(
    source_build_config: Optional[docker_builder.SourceBuildConfig],
    target: Optional[str],
    expected_dockerfile: str,
):
    base_uri = docker_builder.ImageURI.from_uri(_BASE_IMAGE_URI)
    dockerfile_full_path = os.path.join(_RESOURCE_PATH, expected_dockerfile)

    with open(dockerfile_full_path, "rt") as f:
        expected_contents = f.read().strip()

    actual_contents = docker_builder._generate_dockerfile_contents(
        base_uri=base_uri,
        source_build_config=source_build_config,
        target=target,
    )

    assert actual_contents == expected_contents


def test_execute_build_script_happy(caplog: Any):
    target = "/dummy.py"
    image_script = os.path.join(_RESOURCE_PATH, "good_image_script.sh")
    expected_image_uri = docker_builder.ImageURI.from_uri(uri=_BASE_IMAGE_URI)

    actual_image_uri = docker_builder._execute_build_script(
        target=target, image_script=image_script
    )

    assert actual_image_uri == expected_image_uri


def test_execute_build_script_error():
    target = "/dummy.py"
    image_script = os.path.join(_RESOURCE_PATH, "bad_image_script.sh")

    with pytest.raises(
        docker_builder.BuildError, match="Unable to source container image URI from.*42"
    ):
        docker_builder._execute_build_script(target=target, image_script=image_script)


def test_push_image_happy(mock_image: mock.Mock, mock_docker_client: mock.Mock):
    image_uri = docker_builder.ImageURI.from_uri(_BASE_IMAGE_URI)
    expected_remote_uri = docker_builder.ImageURI.from_uri(_REMOTE_IMAGE_URI)

    actual_remote_uri = docker_builder._push_image(
        image=mock_image,
        image_uri=image_uri,
        push_config=_PUSH_CONFIG,
        docker_client=mock_docker_client,
    )

    assert actual_remote_uri == expected_remote_uri
    mock_image.tag.assert_called_once()
    mock_image.reload.assert_called_once()
    mock_docker_client.images.push.assert_called_once_with(
        repository=_PUSH_CONFIG.get_repository_str(),
        tag=_PUSH_CONFIG.get_tag(),
        stream=True,
        decode=True,
    )


def test_push_image_skip(mock_image: mock.Mock, mock_docker_client: mock.Mock):
    image_uri = docker_builder.ImageURI.from_uri(_BASE_IMAGE_URI)

    actual_remote_uri = docker_builder._push_image(
        image=mock_image,
        image_uri=image_uri,
        push_config=None,
        docker_client=mock_docker_client,
    )

    assert actual_remote_uri == image_uri
    mock_image.tag.assert_not_called()
    mock_image.reload.assert_not_called()
    mock_docker_client.images.push.assert_not_called()


def test_push_image_tagging_failed(
    mock_image: mock.Mock, mock_docker_client: mock.Mock
):
    image_uri = docker_builder.ImageURI.from_uri(_BASE_IMAGE_URI)
    mock_image.tag.return_value = False

    with pytest.raises(docker_builder.BuildError, match="Tagging image.*failed.*"):
        docker_builder._push_image(
            image=mock_image,
            image_uri=image_uri,
            push_config=_PUSH_CONFIG,
            docker_client=mock_docker_client,
        )

    mock_image.tag.assert_called_once()
    mock_image.reload.assert_not_called()
    mock_docker_client.images.push.assert_not_called()


def test_push_image_pushing_failed(
    mock_image: mock.Mock, mock_docker_client: mock.Mock, caplog: Any
):
    image_uri = docker_builder.ImageURI.from_uri(_BASE_IMAGE_URI)
    mock_docker_client.images.push.return_value = [
        {"id": 1, "status": "Preparing"},
        {"error": "didn't work", "errorDetail": "it hit the fan"},
    ]

    with caplog.at_level(logging.ERROR):
        with pytest.raises(
            docker_builder.BuildError, match="Unable to push image: didn't work"
        ):
            docker_builder._push_image(
                image=mock_image,
                image_uri=image_uri,
                push_config=_PUSH_CONFIG,
                docker_client=mock_docker_client,
            )

        assert_logs_captured(caplog, "Image push error details: 'it hit the fan'")

    mock_image.tag.assert_called_once()
    mock_image.reload.assert_not_called()
    mock_docker_client.images.push.assert_called_once_with(
        repository=_PUSH_CONFIG.get_repository_str(),
        tag=_PUSH_CONFIG.get_tag(),
        stream=True,
        decode=True,
    )


def test_reload_image_uri(mock_image: mock.Mock):
    # check that building a pipeline from scratch works
    actual_uri = docker_builder._reload_image_uri(mock_image)
    assert repr(actual_uri) == _REMOTE_IMAGE_URI
    mock_image.reload.assert_called_once()

    # check that rebuilding a pipeline works
    actual_uri = docker_builder._reload_image_uri(mock_image)
    assert repr(actual_uri) == _REMOTE_IMAGE_URI
    mock_image.reload.assert_called()


def test_docker_status_update_to_str():
    actual_str = docker_builder._docker_status_update_to_str({})
    assert actual_str is None

    actual_str = docker_builder._docker_status_update_to_str({"k1": " v1 "})
    assert actual_str == "k1=v1"

    actual_str = docker_builder._docker_status_update_to_str({"k1": " v1 ", "k2": ""})
    assert actual_str == "k1=v1 k2="


def test_get_local_image_name():
    mock_build_config = mock.Mock(docker_builder.BuildConfig)

    mock_build_config.push = None
    actual_name = docker_builder._get_local_image_name(
        target=_LAUNCH_SCRIPT, build_config=mock_build_config
    )

    assert actual_name == "fixtures:default"

    mock_build_config.push = _PUSH_CONFIG
    actual_name = docker_builder._get_local_image_name(
        target=_LAUNCH_SCRIPT, build_config=mock_build_config
    )

    assert actual_name == _LOCAL_IMAGE_NAME
