"""
The native Docker Builder plugin implementation.
"""
# Standard Library
import distutils.util
import glob
import json
import logging
import os
import re
import runpy
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

# isort: off

# Third-party
import docker
import yaml

# there is a collision between the docker-py library and the sematic/docker directory,
# so we need to add `# type: ignore` everywhere a component of the docker module is used
from docker.models.images import Image  # type: ignore

# isort: on

# Sematic
from sematic.abstract_plugin import SEMATIC_PLUGIN_AUTHOR, PluginVersion
from sematic.container_images import CONTAINER_IMAGE_ENV_VAR
from sematic.plugins.abstract_builder import (
    AbstractBuilder,
    BuildConfigurationError,
    BuildError,
)

logger = logging.getLogger(__name__)

# Version of the build file schema
# TODO: bump to 1 when the build system is exposed to users
BUILD_SCHEMA_VERSION = 0

# TODO: bump to 0.1.0 when the build system is exposed to users
_PLUGIN_VERSION = (0, 0, 1)

_DOCKERFILE_BASE_TEMPLATE = """
FROM {base_uri}
WORKDIR /

RUN which pip3 || apt update -y && apt install -y python3-pip
RUN python3 -c "import distutils" || apt update -y && apt install --reinstall -y python$(python3 -c "import sys; print(f'{{sys.version_info.major}}.{{sys.version_info.minor}}')")-distutils

ENV PATH="/sematic/bin/:${{PATH}}"
RUN echo '#!/bin/sh' > entrypoint.sh && echo '/usr/bin/python3 -m sematic.resolvers.worker "$@"' >> entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
"""  # noqa: E501

_DOCKERFILE_REQUIREMENTS_TEMPLATE = """
COPY {requirements_file} requirements.txt
RUN pip3 install --no-cache -r requirements.txt
"""


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
        match = re.match("(.+):(.+)@(.+)", uri)

        if match is None:
            raise BuildConfigurationError(
                f"Container image URI '{uri}' does not conform to the required "
                f"`<repository>:<tag>@<digest>` format!"
            )

        return ImageURI(
            repository=match.group(1), tag=match.group(2), digest=match.group(3)
        )

    @classmethod
    def from_image(cls, image: Image) -> "ImageURI":
        """
        Returns an `ImageURI` that identifies the specified image.

        Raises
        ------
        ValueError:
            The specified image does not have a defined repository/tag, which is required
            for generating a URI in the `<repository>:<tag>@<digest>` format.
        """
        if len(image.attrs.get("RepoTags", [])) == 0:
            raise ValueError(
                f"Container image '{image.id}' does not have a defined tag!"
            )

        repository, tag = image.attrs["RepoTags"][0].split(":")
        return ImageURI(repository=repository, tag=tag, digest=image.id)

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
        if self.tls is not None and isinstance(self.tls, str):
            # TODO: extract settings.as_bool to utilities, and use that instead
            self.tls = bool(distutils.util.strtobool(self.tls))
        if self.credstore_env is not None and isinstance(self.credstore_env, str):
            self.credstore_env = json.loads(self.credstore_env)
        if self.use_ssh_client is not None and isinstance(self.use_ssh_client, str):
            # TODO: extract settings.as_bool to utilities, and use that instead
            self.use_ssh_client = bool(distutils.util.strtobool(self.use_ssh_client))
        if self.max_pool_size is not None and isinstance(self.max_pool_size, str):
            self.max_pool_size = int(self.max_pool_size)


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

        # TODO: switch from project-relative paths to build file-relative paths,
        #  and mangle these path fields
        # TODO: validate absolute paths are not used

    @classmethod
    def load_build_config_file(cls, build_file_path: str) -> "BuildConfig":
        """
        Loads the contents of a build configuration file, and returns a `BuildConfig`
        object.

        Raises
        ------
        BuildConfigurationError:
            An error occurred during loading or interpreting of the build file.
        """
        try:
            with open(build_file_path, "r") as f:
                loaded_yaml = yaml.load(f, yaml.Loader)

            return BuildConfig(**loaded_yaml)

        except Exception as e:
            raise BuildConfigurationError(
                f"Unable to load build configuration from '{build_file_path}': {e}"
            ) from e


class DockerBuilder(AbstractBuilder):
    """
    Docker-based Build System plugin implementation.

    Packages the target Pipeline code and required dependencies in a Docker image,
    according to a proprietary build configuration specified via a configuration file of
    the form:

    ```
    version: <version>
    base_uri: <base image URI>
    image_script: <custom image URI script>
    build:
        requirements: <requirements file>
        data: <list of data file globs>
        src: <list of source file globs>
    push:
        registry: <image push registry>
        repository: <image push repository>
        tag_suffix: <optional image push tag suffix>
    ```

    It then launches the target Pipeline by submitting its execution to Sematic Server,
    using the build image to execute `@func`s in the cloud.
    """

    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    def build_and_launch(self, target: str) -> None:
        """
        Builds a container image and launches the specified target launch script, based on
        proprietary build configuration files.

        Parameters
        ----------
        target: str
            The path to the Pipeline target to launch; the built image must support this
            target's execution.

        Raises
        ------
        BuildError:
            There was an error when executing the specified build script.
        BuildConfigurationError:
            There was an error when validating the specified build configuration.
        SystemExit:
            A subprocess exited with an unexpected code.
        """
        image_uri = _build(target=target)
        _launch(target=target, image_uri=image_uri)


def _build(target: str) -> ImageURI:
    """
    Builds the container image, returning the image URI that can be used to launch
    executions.
    """
    build_config = _get_build_config(script_path=target)
    logger.info("Loaded build configuration: %s", build_config)

    docker_client = _make_docker_client(build_config.docker)
    logger.info("Instantiated docker client for server: %s", docker_client.api.base_url)

    image, image_uri = _build_image(
        target=target, build_config=build_config, docker_client=docker_client
    )
    logger.info("Built local image: %s", repr(image_uri))

    build_image_uri = _push_image(
        image=image,
        image_uri=image_uri,
        push_config=build_config.push,
        docker_client=docker_client,
    )

    logger.info("Using image: %s", repr(build_image_uri))

    return build_image_uri


def _launch(target: str, image_uri: ImageURI) -> None:
    """
    Launches the specified user code target, using the specified image.
    """
    sys.path.append(os.getcwd())
    # TODO: revert this overwrite after finishing execution
    #  promote the `environment_variables` testing fixture to a utility
    os.environ[CONTAINER_IMAGE_ENV_VAR] = repr(image_uri)

    logger.info("Launching target: '%s'", target)

    runpy.run_path(path_name=target, run_name="__main__")

    logger.info("Finished launching target: '%s'", target)


def _get_build_config(script_path: str) -> BuildConfig:
    """
    Handles the entire instantiation of the definite `BuildConfig` object for the
    specified script.

    Raises
    ------
    BuildConfigurationError:
        There was an error when loading or validating the specified build configuration.
    """
    build_config_files = _find_build_config_files(script_path=script_path)
    logger.info(
        "Script '%s' has these corresponding build files: %s",
        script_path,
        build_config_files,
    )

    # TODO: override several config files, env vars, and cli arguments
    if len(build_config_files) == 0:
        raise BuildConfigurationError(
            f"Unable to find any build files corresponding to script '{script_path}'! "
            f"Please see TODO for build configuration details!"
        )

    return BuildConfig.load_build_config_file(build_config_files[0])


def _find_build_config_files(script_path: str) -> List[str]:
    """
    Searches for build configuration files that correspond to the specified script file,
    and returns a list containing their paths.
    """
    # TODO: also load `sematic_build.yaml` files on the file hierarchy between the cwd and
    #  the script directory
    root = os.path.splitext(script_path)[0]
    file_candidate = f"{root}.yaml"

    return [file_candidate] if os.path.isfile(file_candidate) else []


def _make_docker_client(
    docker_config: Optional[DockerClientConfig],
) -> docker.DockerClient:  # type: ignore
    """
    Instantiates a `DockerClient` based on the specified configuration.

    If no configuration is passed, uses the system Docker Client configuration.
    """
    try:
        if docker_config is None:
            return docker.from_env()  # type: ignore

        kwargs = {k: v for k, v in asdict(docker_config).items() if v is not None}
        return docker.DockerClient(**kwargs)  # type: ignore

    except docker.errors.DockerException as e:  # type: ignore
        raise BuildError(f"Unable to instantiate Docker client: {e}") from e


def _build_image(
    target: str,
    build_config: BuildConfig,
    docker_client: docker.DockerClient,  # type: ignore
) -> Tuple[Image, ImageURI]:
    """
    Builds the container image to use, according to the build configuration, and returns
    an `ImageURI` that identifies it.

    Parameters
    ----------
    target: str
        The path to the Pipeline target to launch; the built image must support this
        target's execution.
    build_config: BuildConfig
        The configuration that controls the image build.
    docker_client: docker.DockerClient
        The client to use for executing the operations.

    Returns
    -------
    Tuple[Image, ImageURI]:
        The build container image and a URI that identifies the image.

    Raises
    ------
    BuildError:
        There was an error when building the image.
    BuildConfigurationError:
        There was an error when validating the specified build configuration.
    SystemExit:
        A subprocess exited with an unexpected code.
    """
    effective_base_uri = build_config.base_uri

    if build_config.image_script is not None:
        effective_base_uri = _execute_build_script(
            target=target, image_script=build_config.image_script
        )

    # appease mypy
    assert effective_base_uri is not None

    return _build_image_from_base(
        target=target,
        effective_base_uri=effective_base_uri,
        build_config=build_config,
        docker_client=docker_client,
    )


def _build_image_from_base(
    target: str,
    effective_base_uri: ImageURI,
    build_config: BuildConfig,
    docker_client: docker.DockerClient,  # type: ignore
) -> Tuple[Image, ImageURI]:
    """
    Builds the container image to use by adding layers to an existing base image.
    """
    built_image_name = _get_local_image_name(target=target, build_config=build_config)
    logger.info(
        "Building image '%s' starting from base: %s",
        built_image_name,
        effective_base_uri,
    )

    dockerfile_contents = _generate_dockerfile_contents(
        base_uri=effective_base_uri,
        source_build_config=build_config.build,
        target=target if build_config.base_uri is not None else None,
    )
    logger.debug("Using Dockerfile:\n%s", dockerfile_contents)

    # we have to create a tmp dockerfile and pass it instead of using the `fileobj` option
    # of the docker_client, because it does not work with contexts, so operations like
    # COPY do not work, as there exists no working dir context to copy the targets from
    # API: https://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.build
    # Reported unresolved issue: https://github.com/docker/docker-py/issues/2105
    with tempfile.NamedTemporaryFile(mode="wt", delete=True) as dockerfile:
        dockerfile.write(dockerfile_contents)
        dockerfile.flush()

        optional_kwargs = dict()
        if build_config.build is not None and build_config.build.platform is not None:
            optional_kwargs["platform"] = build_config.build.platform

        status_updates = docker_client.api.build(
            dockerfile=dockerfile.name,
            # use the project root as the context
            # TODO: switch from project-relative paths to build file-relative paths
            path=os.getcwd(),
            tag=built_image_name,
            decode=True,
            **optional_kwargs,
        )

    if status_updates is None:
        logger.warning("Built image '%s' without any response", built_image_name)
        image = docker_client.images.get(str(effective_base_uri))
        return image, ImageURI.from_image(image)

    for status_update in status_updates:
        if "error" in status_update.keys():
            logger.error(
                "Image build error details: '%s'", str(status_update.get("errorDetail"))
            )
            raise BuildError(
                f"Unable to build image '{built_image_name}': {status_update['error']}"
            )

        update_str = _docker_status_update_to_str(status_update)
        if update_str is not None:
            logger.info("Image build update: %s", update_str)

    image = docker_client.images.get(built_image_name)
    return image, ImageURI.from_image(image)


def _generate_dockerfile_contents(
    base_uri: ImageURI,
    source_build_config: Optional[SourceBuildConfig],
    target: Optional[str],
) -> str:
    """
    Generates the Dockerfile contents based on the config, using templates.

    If the `target` parameter is specified, then the Dockerfile will be generated to copy
    it even if no other source files are specified.
    """
    dockerfile_contents = _DOCKERFILE_BASE_TEMPLATE.format(base_uri=base_uri)

    if source_build_config is not None and source_build_config.requirements is not None:
        logger.debug("Adding requirements file: %s", source_build_config.requirements)
        requirements_contents = _DOCKERFILE_REQUIREMENTS_TEMPLATE.format(
            requirements_file=source_build_config.requirements
        )
        dockerfile_contents = f"{dockerfile_contents}{requirements_contents}"

    if source_build_config is not None and source_build_config.data is not None:
        logger.debug("Adding data files: %s", source_build_config.data)
        for data_glob in source_build_config.data:
            data_files = glob.glob(data_glob)
            if len(data_files) > 0:
                # sorting for determinism
                for data_file in sorted(data_files):
                    dockerfile_contents = (
                        f"{dockerfile_contents}\nCOPY {data_file} {data_file}"
                    )
        # provide an empty line between data and src, for readability
        dockerfile_contents = f"{dockerfile_contents}\n"

    if source_build_config is not None and source_build_config.src is not None:
        logger.debug("Adding source files: %s", source_build_config.src)
        for src_glob in source_build_config.src:
            src_files = glob.glob(src_glob)
            if len(src_files) > 0:
                # sorting for determinism
                for src_file in sorted(src_files):
                    dockerfile_contents = (
                        f"{dockerfile_contents}\nCOPY {src_file} {src_file}"
                    )
    elif target is not None:
        logger.debug("Adding target source file: %s", target)
        dockerfile_contents = f"{dockerfile_contents}\nCOPY {target} {target}"

    return dockerfile_contents.strip()


def _execute_build_script(target: str, image_script: str) -> ImageURI:
    """
    Builds the container image to use by executing the specified script.
    """
    try:
        script_dir, script_file = os.path.split(image_script)
        if script_dir == "":
            script_dir = None  # type: ignore
        script_file = f"./{script_file}"

        logger.info(
            f"Executing: executable={script_file} cwd={script_dir} args={target}"
        )

        # the subprocess' stderr will be inherited from the current process,
        # so it will print directly to the logs
        with subprocess.Popen(
            executable=script_file,
            cwd=script_dir,
            args=target,
            stdout=subprocess.PIPE,
            text=True,
        ) as subproc:

            raw_uri, _ = subproc.communicate()

            if subproc.returncode != 0:
                raise SystemExit(subproc.returncode)

            return ImageURI.from_uri(uri=raw_uri.strip())

    except BaseException as e:
        raise BuildError(
            f"Unable to source container image URI from '{image_script}': {e}"
        ) from e


def _push_image(
    image: Image,  # type: ignore
    image_uri: ImageURI,
    push_config: Optional[ImagePushConfig],
    docker_client: docker.DockerClient,  # type: ignore
) -> ImageURI:
    """
    Re-tags and pushes the image to the configured repository.

    Updates the `image` through lateral effect!

    Parameters
    ----------
    image: Image
        The image to push
    image_uri: ImageURI
        The initial URI of the image to push
    push_config: Optional[ImagePushConfig]
        Instructions where to push the image
    docker_client: docker.DockerClient
        The `DockerClient` to use to execute the operations

    Returns
    -------
    ImageURI:
        The new `ImageURI` that indicates the location where the `image` was pushed.

    Raises
    ------
    BuildError:
        There was an error when executing the `docker` commands.
    """
    if push_config is None:
        logger.info("Image pushing not configured; skipping")
        return image_uri

    repository = push_config.get_repository_str()
    tag = push_config.get_tag()

    tagging_successful = image.tag(repository=repository, tag=tag)

    if not tagging_successful:
        raise BuildError(
            f"Tagging image '{image_uri}' in repository '{repository}' "
            f"with tag '{tag}' failed; no other information available."
        )

    logger.info(
        "Tagged image '%s' in repository '%s' with tag '%s'", image_uri, repository, tag
    )

    status_updates = docker_client.images.push(
        repository=repository, tag=tag, stream=True, decode=True
    )

    if status_updates is None:
        logger.warning(
            "Pushed image '%s' to repository '%s' with tag '%s', without any response",
            image_uri,
            repository,
            tag,
        )
        return _reload_image_uri(image=image)

    for status_update in status_updates:
        if "error" in status_update.keys():
            logger.error(
                "Image push error details: '%s'", str(status_update.get("errorDetail"))
            )
            raise BuildError(f"Unable to push image: {status_update['error']}")

        update_str = _docker_status_update_to_str(status_update)
        if update_str is not None:
            logger.info("Image push update: %s", update_str)

    return _reload_image_uri(image=image)


def _reload_image_uri(image: Image) -> ImageURI:  # type: ignore
    """
    Reloads an image's tags and digest after it has been pushed to a repository, returning
    an `ImageURI` that locates it in that repository.
    """
    image.reload()
    while len(image.attrs["RepoDigests"]) == 0:
        logger.debug("Reloading image...")
        time.sleep(1)
        image.reload()

    # couldn't find any better way of doing this
    # we know "RepoTags" and "RepoDigests" exist because we just pushed the image,
    # filling in those attrs
    digest = image.attrs["RepoDigests"][0].split("@")[1]
    # "RepoDigests" does not contain the fully qualified repo and tag;
    # we must use "RepoTags"
    repository, tag = image.attrs["RepoTags"][0].split(":")

    return ImageURI(repository=repository, tag=tag, digest=digest)


def _docker_status_update_to_str(status_update: Dict[str, Any]) -> Optional[str]:
    """
    Returns a textual representation of the status update dict received from the Docker
    server, or None if it was devoid of useful information.
    """
    length = len(status_update)

    if length == 0:
        return None

    if length == 1:
        k, v = next(iter(status_update.items()))
        if v is None or len(str(v).strip()) == 0:
            # only one key with an empty value
            return None
        return f"{k}={str(v).strip()}"

    return " ".join(sorted([f"{k}={str(v).strip()}" for k, v in status_update.items()]))


def _get_local_image_name(target: str, build_config: BuildConfig) -> str:
    """
    Returns a local name to give to an image build for the specified target script,
    according to the specified build configuration.
    """
    # TODO: switch from project-relative paths to build file-relative paths
    dir_name = os.path.basename(os.path.dirname(os.path.abspath(target)))
    if dir_name == "/":
        dir_name = "default"

    if build_config.push is None:
        return f"{dir_name}:default"

    return f"{dir_name}:{build_config.push.get_tag()}"
