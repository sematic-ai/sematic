# Standard Library
import os

# Third-party
import pytest

# Sematic
from sematic.plugins.building import docker_builder_config


# this is the relative path inside the bazel sandbox where the data files will be copied
# they are repo-relative instead of build file-relative
RESOURCE_PATH = os.path.join("sematic", "plugins", "building", "tests", "fixtures")
LAUNCH_SCRIPT = os.path.join(RESOURCE_PATH, "good_launch_script.py")
IMAGE_SHA = "sha256:bea3926876a3024c33fe08e0a6b2c0377a7eb600d7b3061a3f3f39d711152e3c"


def test_image_uri_happy():
    image_uri = docker_builder_config.ImageURI.from_uri("a:b@c")

    assert image_uri.repository == "a"
    assert image_uri.tag == "b"
    assert image_uri.digest == "c"
    assert str(image_uri) == "a:b"
    assert repr(image_uri) == "a:b@c"

    image_uri = docker_builder_config.ImageURI.from_uri("'ab:cd@ef'")

    assert image_uri.repository == "ab"
    assert image_uri.tag == "cd"
    assert image_uri.digest == "ef"
    assert str(image_uri) == "ab:cd"
    assert repr(image_uri) == "ab:cd@ef"

    image_uri = docker_builder_config.ImageURI.from_uri('"a:b@sha256:c"')

    assert image_uri.repository == "a"
    assert image_uri.tag == "b"
    assert image_uri.digest == "sha256:c"
    assert str(image_uri) == "a:b"
    assert repr(image_uri) == "a:b@sha256:c"


def test_image_uri_malformed():
    with pytest.raises(
        docker_builder_config.BuildConfigurationError,
        match=".*does not conform to the required.*",
    ):
        docker_builder_config.ImageURI.from_uri("a:b")

    with pytest.raises(
        docker_builder_config.BuildConfigurationError,
        match=".*does not conform to the required.*",
    ):
        docker_builder_config.ImageURI.from_uri("a'b:c@sha256:d")


def test_validate_paths_happy():
    docker_builder_config._validate_paths(paths=None)
    docker_builder_config._validate_paths(
        paths=["a", "./b", "//c", "d/e/f", "**/g", "*.h", "i/../j", "k/l/**/m/n*"]
    )


def test_validate_paths_error():
    with pytest.raises(
        docker_builder_config.BuildConfigurationError,
        match="Paths cannot be absolute.*",
    ):
        docker_builder_config._validate_paths(
            paths=["a", "./b", "//c", "d/e/f", "/abs/a/b/c"]
        )


def test_normalize_paths_happy():
    raw_paths = ["a", "./b", "//c", "d/e/f", "**/g", "*.h", "i/../j", "k/l/**/m/n*"]
    expected_normalized_paths = [
        "root/a",
        "root/b",
        "c",
        "root/d/e/f",
        "root/**/g",
        "root/*.h",
        "root/j",
        "root/k/l/**/m/n*",
    ]

    actual_normalized_paths = docker_builder_config._normalize_paths(
        relative_path="root", paths=raw_paths
    )

    assert actual_normalized_paths == expected_normalized_paths


def test_normalize_paths_error():
    with pytest.raises(
        docker_builder_config.BuildConfigurationError,
        match="Paths must be within the project root file structure.*",
    ):
        docker_builder_config._normalize_paths(
            relative_path="root", paths=["phony/../../../home/bob"]
        )


def test_find_build_config_files_happy():
    script_path = os.path.join(RESOURCE_PATH, "nested", "launch_script.py")
    expected_build_config_files = [
        os.path.join(RESOURCE_PATH, "sematic_build.yaml"),
        os.path.join(RESOURCE_PATH, "nested", "sematic_build.yaml"),
        os.path.join(RESOURCE_PATH, "nested", "launch_script.yaml"),
    ]

    actual_build_config_files = docker_builder_config._find_build_config_files(
        script_path=script_path
    )

    assert actual_build_config_files == expected_build_config_files


@pytest.mark.parametrize(
    "config_file,match",
    [
        ("/abs.py", "The launch script path must be relative to the project root.*"),
        ("inexistent.py", "Launch script path not found or unreadable.*"),
        ("good_minimal.yaml", "The launch script must be a python file.*"),
        ("not_executable", "The launch script must be a python file.*"),
    ],
)
def test_find_build_config_files_errors(config_file: str, match: str):
    build_file_path = os.path.join(RESOURCE_PATH, config_file)

    with pytest.raises(docker_builder_config.BuildConfigurationError, match=match):
        docker_builder_config._find_build_config_files(script_path=build_file_path)


def test_load_build_config_full_base_uri_happy():
    actual_config = docker_builder_config.load_build_config(script_path=LAUNCH_SCRIPT)

    assert actual_config is not None
    assert actual_config.version == docker_builder_config.BUILD_SCHEMA_VERSION
    assert actual_config.image_script is None
    assert actual_config.base_uri is not None
    assert actual_config.base_uri.repository == "sematicai/sematic-worker-base"
    assert actual_config.base_uri.tag == "latest"
    assert actual_config.base_uri.digest == IMAGE_SHA
    assert actual_config.build is not None
    assert actual_config.build.platform == "linux/amd64"
    assert actual_config.build.requirements == (
        "sematic/plugins/building/tests/fixtures/requirements.txt"
    )
    # check relative, project-relative, and "../" path resolution
    # check globbing and wildcards
    assert actual_config.build.data == [
        "sematic/plugins/building/tests/fixtures/docker",
        "sematic/plugins/building/tests/fixtures/*.sh",
        "sematic/plugins/building/tests/fixtures/no_image*",
        "sematic/plugins/building/tests/**/two_images*",
        "sematic/plugins/building/tests/fixtures/**/third_level.*",
    ]
    assert actual_config.build.src == ["sematic/plugins/building/tests/fixtures/*.py"]
    assert actual_config.push is not None
    assert actual_config.push.registry == "my_registry.com"
    assert actual_config.push.repository == "my_repository"
    assert actual_config.push.tag_suffix == "my_tag_suffix"
    assert actual_config.docker.base_url == "unix://var/run/docker.sock"
    assert actual_config.docker.credstore_env == {
        "DOCKER_TLS_VERIFY": "/home/trudy/legit.cer"
    }


def test_load_build_config_minimal_image_script_happy():
    build_file_path = os.path.join(RESOURCE_PATH, "good_minimal.yaml")
    expected_image_script = os.path.join(RESOURCE_PATH, "good_image_script.sh")

    actual_config = docker_builder_config.BuildConfig.load_build_config_file(
        build_file_path=build_file_path
    )

    assert actual_config is not None
    assert actual_config.version == docker_builder_config.BUILD_SCHEMA_VERSION
    assert actual_config.image_script == expected_image_script
    assert actual_config.base_uri is None
    assert actual_config.build is None
    assert actual_config.push is None


@pytest.mark.parametrize(
    "config_file,match",
    [
        ("bad_version.yaml", ".*Unsupported build schema version.*"),
        ("absolute_data.yaml", "Paths cannot be absolute.*"),
        ("absolute_src.yaml", "Paths cannot be absolute.*"),
        ("absolute_requirements.yaml", "Paths cannot be absolute.*"),
        (
            "jailbreak_data.yaml",
            "Paths must be within the project root file structure.*",
        ),
        (
            "jailbreak_src.yaml",
            "Paths must be within the project root file structure.*",
        ),
        (
            "jailbreak_requirements.yaml",
            "Paths must be within the project root file structure.*",
        ),
        ("no_image.yaml", "Exactly one of `image_script` and `base_uri`.*"),
        ("two_images.yaml", "Exactly one of `image_script` and `base_uri`.*"),
        ("malformed_uri.yaml", ".*does not conform to the required.*"),
        (
            "malformed_push_empty_registry.yaml",
            ".*`registry` and `repository` must be non-empty.*",
        ),
        (
            "malformed_push_missing_repository.yaml",
            ".*missing 1 required positional argument: 'repository'",
        ),
    ],
)
def test_load_build_config_errors(config_file: str, match: str):
    build_file_path = os.path.join(RESOURCE_PATH, config_file)

    with pytest.raises(docker_builder_config.BuildConfigurationError, match=match):
        docker_builder_config.BuildConfig.load_build_config_file(
            build_file_path=build_file_path
        )


def test_load_build_config_merge_and_normalize_w_specific_config():
    script_path = os.path.join(RESOURCE_PATH, "nested", "launch_script.py")
    expected_config = docker_builder_config.BuildConfig(
        version=1,
        image_script=None,
        base_uri=docker_builder_config.ImageURI.from_uri("d:e@f"),
        build=docker_builder_config.SourceBuildConfig(
            platform="linux/amd64",
            requirements=os.path.join(RESOURCE_PATH, "requirements.txt"),
            data=[
                os.path.join(RESOURCE_PATH, "nested", "**/*.txt"),
                os.path.join(RESOURCE_PATH, "nested", "**/*.dat"),
            ],
            src=[os.path.join(RESOURCE_PATH, "nested", "**/*.py")],
        ),
        push=None,
        docker=None,
    )

    actual_config = docker_builder_config.load_build_config(script_path=script_path)
    assert actual_config == expected_config


def test_load_build_config_merge_and_normalize_no_specific_config():
    script_path = os.path.join(
        RESOURCE_PATH, "nested", "launch_script_no_specific_config.py"
    )
    expected_config = docker_builder_config.BuildConfig(
        version=1,
        image_script=os.path.join(RESOURCE_PATH, "good_image_script.sh"),
        base_uri=None,
        build=docker_builder_config.SourceBuildConfig(
            platform="linux/amd64",
            requirements="sematic/plugins/building/tests/fixtures/requirements.txt",
            data=[os.path.join(RESOURCE_PATH, "nested", "**/*.txt")],
            src=None,
        ),
        push=None,
        docker=None,
    )

    actual_config = docker_builder_config.load_build_config(script_path=script_path)
    assert actual_config == expected_config
