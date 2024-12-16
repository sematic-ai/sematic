"""
The native Docker Builder plugin configuration file management module.
"""

# Standard Library
import functools
import json
import logging
import os
import re
from dataclasses import asdict, dataclass, replace
from typing import Any, Dict, List, Optional

# Third-party
import yaml

# Sematic
from sematic.plugins.abstract_builder import BuildConfigurationError
from sematic.utils.types import as_bool


logger = logging.getLogger(__name__)

# Version of the build file schema
BUILD_SCHEMA_VERSION = 1
# this is the standard build configuration file name
_BUILD_CONFIG_FILE_NAME = "sematic_build.yaml"
# paths beginning with this prefix will be considered project-relative
_PROJECT_ROOT_PREFIX = "//"
_PARENT_PATH_ELEMENT = ".."


_URI_QUOTES = "[\"']"
_URI_NON_RESERVED_CHARS = "[^\"'@:]"
_URI_TAGGED_IMAGE = f"({_URI_NON_RESERVED_CHARS}+):({_URI_NON_RESERVED_CHARS}+)"
_URI_DIGEST = f"{_URI_NON_RESERVED_CHARS}+:?{_URI_NON_RESERVED_CHARS}*"
_URI_TAGGED_IMAGE_WITH_DIGEST = f"{_URI_TAGGED_IMAGE}@({_URI_DIGEST})"
_URI_REGEX = f"{_URI_QUOTES}?{_URI_TAGGED_IMAGE_WITH_DIGEST}{_URI_QUOTES}?"


@dataclass
class ImageURI:
    """
    A URI that uniquely identifies a container image.
    """

    repository: str
    tag: str
    digest: str

    @classmethod
    def from_uri(cls, uri: str) -> "ImageURI":
        """
        Returns an `ImageURI` object based on the supplied URI string.

        Raises
        ------
        BuildConfigurationError:
            The specified value is not a correct and complete container image URI in the
            required `<repository>:<tag>@<digest>` format.
        """
        match = re.match(_URI_REGEX, uri)

        if match is None:
            raise BuildConfigurationError(
                f"Container image URI '{uri}' does not conform to the required "
                f"`<repository>:<tag>@<digest>` format!"
            )

        return ImageURI(
            repository=match.group(1), tag=match.group(2), digest=match.group(3)
        )

    def __str__(self):
        """
        Returns a short `<repository>:<tag>` version of this image URI.
        """
        return f"{self.repository}:{self.tag}"

    def __repr__(self):
        """
        Returns the full image URI in the `<repository>:<tag>@<digest>` format.
        """
        return f"{self.repository}:{self.tag}@{self.digest}"


@dataclass
class SourceBuildConfig:
    """
    A packaged build source file configuration.
    """

    platform: Optional[str] = None
    requirements: Optional[str] = None
    data: Optional[List[str]] = None
    src: Optional[List[str]] = None

    def __post_init__(self):
        """
        Validates the contents of this object.

        Raises
        ------
        BuildConfigurationError:
            At least one of the contained paths is absolute.
        """
        _validate_paths(paths=self.data)
        _validate_paths(paths=self.src)
        if self.requirements is not None:
            _validate_paths(paths=[self.requirements])

    def normalize_paths(self, relative_path: str) -> "SourceBuildConfig":
        """
        The glob paths contained in the configuration will be normalized so that they will
        be relative to the project root.
        """
        kwargs: Dict[str, Any] = {}

        if self.requirements is not None:
            [kwargs["requirements"]] = _normalize_paths(
                relative_path, [self.requirements]
            )

        if self.data is not None:
            kwargs["data"] = _normalize_paths(relative_path, self.data)

        if self.src is not None:
            kwargs["src"] = _normalize_paths(relative_path, self.src)

        return replace(self, **kwargs)

    def merge(self, other: "SourceBuildConfig") -> "SourceBuildConfig":
        """
        Merges this `ImagePushConfig` object with the specified one.
        """
        kwargs: Dict[str, Any] = {}

        if other.platform is not None:
            kwargs["platform"] = other.platform

        if other.requirements is not None:
            kwargs["requirements"] = other.requirements

        if other.data:
            kwargs["data"] = (self.data or []) + other.data

        if other.src:
            kwargs["src"] = (self.src or []) + other.src

        return replace(self, **kwargs)


@dataclass
class ImagePushConfig:
    """
    A packaged build image push configuration.
    """

    registry: str
    repository: str
    tag_suffix: Optional[str] = None

    def __post_init__(self):
        """
        Validates the contents of this object.
        """
        if not self.registry or not self.repository:
            raise BuildConfigurationError(
                "When `push` is specified, `registry` and `repository` must be non-empty!"
            )

    def get_repository_str(self) -> str:
        """
        Returns a string that identifies the repository according to the `docker` library
        naming convention.
        """
        return f"{self.registry}/{self.repository}"

    def get_tag(self) -> str:
        """
        Returns the effective tag to use for the image.
        """
        if not self.tag_suffix:
            return "default"
        return f"default_{self.tag_suffix}"

    def merge(self, other: "ImagePushConfig") -> "ImagePushConfig":
        """
        Merges this `ImagePushConfig` object with the specified one.
        """
        if other.tag_suffix is not None:
            return other
        return replace(other, tag_suffix=self.tag_suffix)


@dataclass
class DockerClientConfig:
    """
    The Docker Client connection details to use to connect to the Docker Server.

    See https://docker-py.readthedocs.io/en/stable/client.html#client-reference for more
    details.
    """

    base_url: str = "unix://var/run/docker.sock"
    version: str = "auto"
    timeout: Optional[int] = None
    tls: bool = False
    user_agent: Optional[str] = None
    credstore_env: Optional[Dict[str, str]] = None
    use_ssh_client: bool = False
    max_pool_size: Optional[int] = None

    def __post_init__(self):
        """
        Validates the contents of this object.
        """
        if self.timeout is not None and isinstance(self.timeout, str):
            self.timeout = int(self.timeout)

        self.tls = as_bool(self.tls)

        if self.credstore_env is not None and isinstance(self.credstore_env, str):
            self.credstore_env = json.loads(self.credstore_env)

        self.use_ssh_client = as_bool(self.use_ssh_client)

        if self.max_pool_size is not None and isinstance(self.max_pool_size, str):
            self.max_pool_size = int(self.max_pool_size)

    def merge(self, other: "DockerClientConfig") -> "DockerClientConfig":
        """
        Merges this `DockerClientConfig` object with the specified one.
        """
        kwargs = {k: v for k, v in asdict(other).items() if v is not None}
        return replace(self, **kwargs)


@dataclass
class BuildConfig:
    """
    A packaged build configuration object that describes how to construct a container
    image that is meant to execute a Runner and Standalone Functions for a specific
    Pipeline.

    Attributes
    ----------
    version: int
        The version of the configuration semantics to which this object adheres.
    image_script: Optional[str]
        An optional path to a script which must write only a container image URI in the
        `<repository>:<tag>@<digest>` format to standard output. This image will be used
        as the base from which the Runner and Standalone Function image will be created.
        Exactly one of `image_script` and `base_uri` must be specified. Defaults to
        `None`.

        This script is meant to be a hook that the user can leverage to build a base
        image. It is the user's responsibility to ensure the resulting base image is
        usable by Sematic in order to construct a Standalone container image:
        - Must contain a `python3` executable in the env `PATH`.
        - Must contain all the source code, data files, and installed Python requirements,
        unless otherwise handled in the `build` field of this configuration.
        - Does not need to specify a workdir, Any specified workdir will be overwritten.
        - Does not need to specify an entry point. Any specified entry point will be
        overwritten.

        The script may write anything to standard error. The script may be written in any
        language supported by the system, as long as it has the executable bit set, and
        the system can determine how to execute it (i.e. specifies a shebang, or is an ELF
        executable).
    base_uri: Optional[ImageURI]
        An optional container image URI in the `<repository>:<tag>@<digest>` format. This
        image will be used as the base from which the Runner and Standalone Function image
        will be created. Exactly one of `image_script` and `base_uri` must be specified.
        Defaults to `None`.
    build: Optional[SourceBuildConfig]
        An object that configures how to package source code, data files, and Python
        requirements inside the container image. Defaults to `None`, meaning nothing with
        be copied to the image, except for the target launch script when using the
        `base_uri` option. When using the `image_script` option, it is the user's
        responsibility to ensure the launch script is present.
    push: Optional[ImagePushConfig]
        An object that configures how to push the resulting container image to registry
        that is accessible from the Sematic Server that will execute the Pipeline.
        Defaults to `None`, meaning that the resulting image will not be pushed to a
        remote registry, and will only be kept on the Docker server user to construct it.
    docker: Optional[DockerClientConfig]
        The Docker Client connection configuration to use to connect to the Docker Server.
        Defaults to `None`, meaning the system Client configuration will be used.
    """

    version: int
    image_script: Optional[str] = None
    base_uri: Optional[ImageURI] = None
    build: Optional[SourceBuildConfig] = None
    push: Optional[ImagePushConfig] = None
    docker: Optional[DockerClientConfig] = None

    def __post_init__(self):
        """
        Validates and casts the contents of this object.

        Raises
        ------
        BuildConfigurationError:
            There was an error when loading the specified build configuration.
        """
        if self.version != BUILD_SCHEMA_VERSION:
            # TODO: implement migration mechanism
            raise BuildConfigurationError(
                f"Unsupported build schema version! Expected: {BUILD_SCHEMA_VERSION}; "
                f"got: {self.version}"
            )

        if (
            self.image_script is None
            and self.base_uri is None
            or self.image_script is not None
            and self.base_uri is not None
        ):
            raise BuildConfigurationError(
                "Exactly one of `image_script` and `base_uri` must be specified!"
            )

        if self.base_uri is not None and isinstance(self.base_uri, str):
            self.base_uri = ImageURI.from_uri(uri=self.base_uri)

        if self.build is not None and isinstance(self.build, dict):
            self.build = SourceBuildConfig(**self.build)

        if self.push is not None and isinstance(self.push, dict):
            self.push = ImagePushConfig(**self.push)

        if self.docker is not None and isinstance(self.docker, dict):
            self.docker = DockerClientConfig(**self.docker)

    def normalize_paths(self, relative_path: str) -> "BuildConfig":
        """
        The paths contained in the configuration will be normalized so that they will be
        relative to the project root.
        """
        kwargs: Dict[str, Any] = {}

        if self.image_script is not None:
            [kwargs["image_script"]] = _normalize_paths(
                relative_path=relative_path, paths=[self.image_script]
            )

        if self.build is not None:
            kwargs["build"] = self.build.normalize_paths(relative_path=relative_path)

        return replace(self, **kwargs)

    def merge(self, other: "BuildConfig") -> "BuildConfig":
        """
        Merges this `BuildConfig` object with the specified one, recursively concatenating
        lists of paths, and overwriting other fields.

        Raises
        ------
        BuildConfigurationError:
            If the two configurations don't share the same schema version.
        """
        if self.version != other.version:
            raise BuildConfigurationError(
                f"Cannot merge build configurations with different versions: "
                f"{self.version} and {other.version}"
            )

        kwargs: Dict[str, Any] = {}

        if other.image_script is not None:
            kwargs["base_uri"] = None
            kwargs["image_script"] = other.image_script

        if other.base_uri is not None:
            kwargs["base_uri"] = other.base_uri
            kwargs["image_script"] = None

        if other.build is not None:
            kwargs["build"] = (
                self.build.merge(other.build) if self.build is not None else other.build
            )

        if other.push is not None:
            kwargs["push"] = (
                self.push.merge(other.push) if self.push is not None else other.push
            )

        if other.docker is not None:
            kwargs["docker"] = (
                self.docker.merge(other.docker)
                if self.docker is not None
                else other.docker
            )

        return replace(self, **kwargs)

    @classmethod
    def load_build_config_file(cls, build_file_path: str) -> "BuildConfig":
        """
        Loads the contents of a build configuration file, and returns a `BuildConfig`
        object.

        The paths contained in the configuration will be normalized so that they will be
        relative to the project root.

        Raises
        ------
        BuildConfigurationError:
            An error occurred during loading or interpreting of the build file.
        """
        try:
            with open(build_file_path, "r") as f:
                loaded_yaml = yaml.load(f, yaml.Loader)

            dir_name = os.path.dirname(build_file_path)
            build_config = BuildConfig(**loaded_yaml)
            build_config = build_config.normalize_paths(relative_path=dir_name)

            return build_config

        except Exception as e:
            raise BuildConfigurationError(
                f"Unable to load build configuration from '{build_file_path}': {e}"
            ) from e

    @classmethod
    def load_build_config_files(cls, build_config_files: List[str]) -> "BuildConfig":
        """
        Loads the contents of the build configuration files, merging their values, and
        returns a `BuildConfig` object.

        Raises
        ------
        BuildConfigurationError:
            An error occurred during loading or interpreting of a build file.
        """
        build_configs = map(cls.load_build_config_file, build_config_files)
        return functools.reduce(lambda c1, c2: c1.merge(c2), build_configs)

    def __repr__(self):
        """
        Returns the complete textual representation of this configuration, as it would
        appear in a configuration file.
        """
        return yaml.dump(asdict(self), Dumper=yaml.Dumper)


def load_build_config(script_path: str) -> BuildConfig:
    """
    Handles the entire instantiation of the definite `BuildConfig` object for the
    specified script.

    Raises
    ------
    BuildConfigurationError:
        There was an error when loading or validating the specified build configuration.
    """
    build_config_files = _find_build_config_files(script_path=script_path)
    logger.debug(
        "Script '%s' has these corresponding build files: %s",
        script_path,
        build_config_files,
    )

    # TODO: override env vars and cli arguments
    if len(build_config_files) == 0:
        raise BuildConfigurationError(
            f"Unable to find any build files corresponding to script '{script_path}'! "
            f"Please see https://docs.sematic.dev/cloud-execution/container-images#docker"
            f" for build configuration details!"
        )

    return BuildConfig.load_build_config_files(build_config_files=build_config_files)


def _find_build_config_files(script_path: str) -> List[str]:
    """
    Searches for build configuration files that correspond to the specified script file,
    and returns a list containing their paths.
    """
    if os.path.isabs(script_path):
        raise BuildConfigurationError(
            f"The launch script path must be relative to the project root; got: "
            f"'{script_path}'"
        )

    if not os.path.isfile(script_path):
        raise BuildConfigurationError(
            f"Launch script path not found or unreadable: '{script_path}'"
        )

    root, extension = os.path.splitext(script_path)
    if extension != ".py":
        raise BuildConfigurationError(
            f"The launch script must be a python file; got: '{script_path}'"
        )

    file_candidate = f"{root}.yaml"
    config_files = []

    # check if there is a config file with the same name as the launch script
    if os.path.isfile(file_candidate) and file_candidate != _BUILD_CONFIG_FILE_NAME:
        config_files.append(file_candidate)

    # walk the dir structure up from the launch script to the project root,
    # checking for build files as we go
    curr_path = script_path
    while len(curr_path) > 0:
        curr_path = os.path.dirname(curr_path)
        file_candidate = os.path.join(curr_path, _BUILD_CONFIG_FILE_NAME)
        if os.path.isfile(file_candidate):
            config_files.append(file_candidate)

    # the config files should start from the project root
    config_files.reverse()
    return config_files


def _validate_paths(paths: Optional[List[str]]) -> None:
    """
    Validates that the specified file paths are not absolute.

    Raises
    ------
    BuildConfigurationError:
        At least one of the specified paths is absolute.
    """
    if paths is not None:
        for path in paths:
            if _is_abs_path(path):
                raise BuildConfigurationError(f"Paths cannot be absolute; got: '{path}'")


def _normalize_paths(relative_path: str, paths: List[str]) -> List[str]:
    """
    The paths contained in the list will be normalized so that they will be relative to
    the project root.

    Raises
    ------
    BuildConfigurationError:
        At least one of the specified paths is outside the project root file system after
        normalization.
    """
    normalized_paths = []

    for path in paths:
        if _is_root_relative_path(path):
            normalized_path = path[2:]
        else:
            normalized_path = os.path.join(relative_path, path)

        # this operation also resolves "../" parent elements
        normalized_path = os.path.normpath(normalized_path)
        # which means that users can attempt to jailbreak out of the project root
        if normalized_path.startswith(_PARENT_PATH_ELEMENT):
            raise BuildConfigurationError(
                f"Paths must be within the project root file structure; got: '{path}'"
            )

        normalized_paths.append(normalized_path)

    return normalized_paths


def _is_root_relative_path(path: str) -> bool:
    """
    Returns whether the specified path is project-relative.
    """
    return path.startswith(_PROJECT_ROOT_PREFIX)


def _is_abs_path(path: str) -> bool:
    """
    Returns whether the specified path is absolute.
    """
    return not _is_root_relative_path(path) and os.path.isabs(path)
