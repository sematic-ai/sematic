"""
The native Docker Builder plugin implementation.
"""
# Standard Library
import glob
import logging
import os
import runpy
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from typing import Any, Dict, Generator, Optional, Tuple

# isort: off

# Third-party
import docker

# there is a collision between the docker-py library and the sematic/docker directory,
# so we need to add `# type: ignore` everywhere a component of the docker module is used
from docker.models.images import Image  # type: ignore

# isort: on

# Sematic
from sematic.abstract_plugin import SEMATIC_PLUGIN_AUTHOR, PluginVersion
from sematic.container_images import CONTAINER_IMAGE_ENV_VAR
from sematic.plugins.abstract_builder import (
    BUILD_CONFIG_ENV_VAR,
    RUN_COMMAND_ENV_VAR,
    AbstractBuilder,
    BuildError,
)
from sematic.plugins.building.docker_builder_config import (
    BuildConfig,
    DockerClientConfig,
    ImagePushConfig,
    ImageURI,
    SourceBuildConfig,
    load_build_config,
)
from sematic.plugins.building.docker_client_utils import rolling_print_status_updates
from sematic.utils.env import environment_variables
from sematic.utils.spinner import stdout_spinner

logger = logging.getLogger(__name__)

_PLUGIN_VERSION = (0, 1, 0)

_DOCKERFILE_BASE_TEMPLATE = """
FROM {base_uri}
WORKDIR /

RUN \
( \
echo '#!/bin/sh' > entrypoint.sh && \
echo '/usr/bin/python3 -m sematic.resolvers.worker "$@"' >> entrypoint.sh && \
chmod +x /entrypoint.sh \
)
ENTRYPOINT ["/entrypoint.sh"]
"""  # noqa: E501

# `pip = 23.1.2` due to: https://github.com/pypa/pip/issues/10851
_DOCKERFILE_ENSURE_PIP_TEMPLATE = """
RUN python3 -c "from distutils import cmd, util" || \
( \
apt-get update -y && \
apt-get install -y --reinstall --no-install-recommends python$(python3 -c "import sys; print(f'{{sys.version_info.major}}.{{sys.version_info.minor}}')")-distutils \
)

RUN which pip || \
( \
export PYTHONDONTWRITEBYTECODE=1 && \
apt-get update -y && \
apt-get install -y --no-install-recommends wget && \
wget --no-verbose -O get-pip.py https://bootstrap.pypa.io/get-pip.py && \
python3 get-pip.py && \
rm get-pip.py && \
unset PYTHONDONTWRITEBYTECODE \
)
"""  # noqa: E501

# `--ignore-installed` due to:
#   `pip cannot uninstall <package>: "It is a distutils installed project"`
_DOCKERFILE_REQUIREMENTS_TEMPLATE = """
COPY {requirements_file} requirements.txt
RUN pip install --no-cache-dir --ignore-installed --root-user-action=ignore -r requirements.txt
"""  # noqa: E501

_DOCKERFILE_ENSURE_SEMATIC = """
RUN python3 -c "import sematic" || \
( \
export PYTHONDONTWRITEBYTECODE=1 && \
pip install --no-cache-dir --ignore-installed --root-user-action=ignore sematic && \
unset PYTHONDONTWRITEBYTECODE \
)

ENV PATH="/sematic/bin/:$PATH"
"""


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
        platform: <docker platform>
        requirements: <requirements file>
        data: <list of data file globs>
        src: <list of source file globs>
    push:
        registry: <image push registry>
        repository: <image push repository>
        tag_suffix: <optional image push tag suffix>
    docker:
        <docker-py configuration arguments>
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

    def build_and_launch(self, target: str, run_command: Optional[str]) -> None:
        """
        Builds a container image and launches the specified target launch script, based on
        proprietary build configuration files.

        Parameters
        ----------
        target: str
            The path to the Pipeline target to launch; the built image must support this
            target's execution.
        run_command: Optional[str]
            The CLI command used to launch the pipeline, if applicable.

        Raises
        ------
        BuildError:
            There was an error when executing the specified build script.
        BuildConfigurationError:
            There was an error when validating the specified build configuration.
        SystemExit:
            A subprocess exited with an unexpected code.
        """
        image_uri, build_config, effective_base_uri = _build(target=target)
        _launch(
            target=target,
            run_command=run_command,
            image_uri=image_uri,
            effective_base_uri=effective_base_uri,
            build_config=build_config,
        )


def _build(target: str) -> Tuple[ImageURI, BuildConfig, ImageURI]:
    """
    Builds the container image, returning the image URI that can be used to launch
    executions, and the build configuration object used to build the image.
    """
    build_config = load_build_config(script_path=target)
    logger.debug("Loaded build configuration: %s", build_config)

    docker_client = _make_docker_client(build_config.docker)
    logger.debug(
        "Instantiated docker client for server: %s", docker_client.api.base_url
    )

    image, image_uri, effective_base_uri = _build_image(
        target=target, build_config=build_config, docker_client=docker_client
    )
    logger.debug("Built local image: %s from base image %s", repr(image_uri), repr(effective_base_uri))

    build_image_uri = _push_image(
        image=image,
        image_uri=image_uri,
        push_config=build_config.push,
        docker_client=docker_client,
    )

    logger.debug("Using image: %s", repr(build_image_uri))

    return build_image_uri, build_config, effective_base_uri


def _launch(
    target: str,
    run_command: Optional[str],
    image_uri: ImageURI,
    effective_base_uri: ImageURI,
    build_config: BuildConfig,
) -> None:
    """
    Launches the specified user code target, using the specified image.
    """
    # ummm sematic.cli.run() w/out build does not modify sys.path ....
    # sys.path.append(os.getcwd())
    logger.info("Launching target: '%s'", target)

    with environment_variables(
        {
            RUN_COMMAND_ENV_VAR: run_command,
            CONTAINER_IMAGE_ENV_VAR: repr(image_uri),
            
            # Maybe this isn't actually needed? it's not read?
            # BUILD_CONFIG_ENV_VAR: repr(build_config),
        }
    ):

        # We really really really really need to actually run in the actual docker image
        # that the user provided so that there is a close similarity between what
        # happens locally and what the k8s pod will do.  Otherwise users can and will
        # get stuck in a really slow iteration cycle to debug things like:
        #  * tools that connect to non-public services like shared filesystems, and the code paths
        #      that run those tools need to be in-container code / binaries versus whatever is
        #      available in parent `sematic run` launching shell.
        #  * native libraries, including user-built native C++ code that might fine in the
        #      shell but needs to be installed properly into a docker to run on the cluster
        #      e.g. with proper LD_LIBRARY_PATH
        #  * torch version and other python packages that might be on the PYTHONPATH of
        #      this shell but do not match the `image_script` env.  for example,
        #      how is the 'intermediate' example here https://github.com/sematic-ai/example_docker/tree/main/intermediate
        #      supposed to work unless the user installs the requirements.txt ?
        #      sure the user can do that, but it's then really easy for the state of their
        #      env to get confused with the env that will get run on the cloud.
        #  * privs of certain files in the docker image
        #  * access keys e.g. AWS keys and access to other services like databases
        #      that might not be dockerized properly
        #  etc etc etc

        if os.environ.get('SEMATIC_IS_RUNNING_IN_DOCKER') == 'True':
            
            # Then we're already in docker and we can launch
            runpy.run_path(path_name=target, run_name="__main__")
        
        else:
            # TODO try to port the command below to docker-py, but the docker-py
            # run() method hasn't really been touched in 7 years according to
            # git blame, so maybe it's better to use the system docker executable anyways

            HOME = os.environ.get('HOME', os.path.expanduser("~"))
            sematic_settings_path = os.path.join(HOME, '.sematic')

            # --env {RUN_COMMAND_ENV_VAR}="{run_command}" \
            #     --env {CONTAINER_IMAGE_ENV_VAR}="{repr(image_uri)}" \
            #     --env {BUILD_CONFIG_ENV_VAR}="{repr(build_config)}" \

            # --build will try to run docker again, which is what we don't want
            run_command_no_build = run_command.replace('--build', '')

            docker_cmd = f"""
                docker run \
                --rm \
                -it \
                --privileged \
                --runtime=nvidia \
                --gpus=all \
                --net=host \
                --env SEMATIC_IS_RUNNING_IN_DOCKER=True \
                --env {CONTAINER_IMAGE_ENV_VAR}="{repr(image_uri)}" \
                --ipc=host \
                -v {sematic_settings_path}/:/root/.sematic:ro \
                -v {os.getcwd()}:/app:z \
                -w /app \
                    {effective_base_uri} {run_command_no_build}
                """
            logger.info(f"Dropping into docker: {docker_cmd}")
            os.execvpe(
                    "docker",
                    docker_cmd.strip().split(),
                    os.environ,
                )

    logger.debug("Finished launching target: '%s'", target)


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
) -> Tuple[Image, ImageURI, ImageURI]:
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
    Tuple[Image, ImageURI, ImageURI]:
        The build container image and a URI that identifies the image, as well as the base URI (non-cloud)
        image for e.g. local execution use.

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

    platform = build_config.build.platform if build_config.build is not None else None

    # attempt to pull previously-existent layers for this image from the remote repo,
    # in order to speed up local-first-time builds and stale builds
    #
    # Q: Why do this and not use the `cache_from` Docker feature?
    # A: Because that feature requires the `BUILDKIT_INLINE_CACHE` flag be set on the
    # image while building, and this seems to require the image to already exist locally,
    # which makes first building an image impossible.
    _pull_existing_layers(
        push_config=build_config.push,
        platform=platform,
        docker_client=docker_client,
    )

    return _build_image_from_base(
        target=target,
        effective_base_uri=effective_base_uri,
        build_config=build_config,
        platform=platform,
        docker_client=docker_client,
    )


def _pull_existing_layers(
    push_config: Optional[ImagePushConfig],
    platform: Optional[str],
    docker_client: docker.DockerClient,  # type: ignore
) -> None:
    """
    Attempts to pull previously existent layers from the configured remote repository
    locally.
    """
    if push_config is None:
        logger.info("Remote repo not configured; skipping image pulling")
        return

    repository = push_config.get_repository_str()
    tag = push_config.get_tag()

    logger.info(
        "Pulling existing layers from repository '%s' with tag '%s'", repository, tag
    )

    optional_kwargs = dict()
    if platform is not None:
        optional_kwargs["platform"] = platform

    try:
        # the call to build below is blocking and takes a while
        # print a spinner in the meantime
        with stdout_spinner():
            status_updates = docker_client.api.pull(
                repository=repository,
                tag=tag,
                stream=True,
                decode=True,
                **optional_kwargs,
            )

        if status_updates is None:
            logger.warning(
                "Pulled existing layers from repository '%s' with tag '%s', "
                "without any response",
                repository,
                tag,
            )
            return

        error_update = rolling_print_status_updates(status_updates)
        if error_update is not None:
            logger.warning(
                "Image pull error details: '%s'", str(error_update.get("errorDetail"))
            )

    except Exception as e:
        logger.warning("Ignoring image pull error: %s", e)


def _build_image_from_base(
    target: str,
    effective_base_uri: ImageURI,
    build_config: BuildConfig,
    platform: Optional[str],
    docker_client: docker.DockerClient,  # type: ignore
) -> Tuple[Image, ImageURI, ImageURI]:
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

    status_updates = _build_from_dockerfile(
        built_image_name=built_image_name,
        dockerfile_contents=dockerfile_contents,
        platform=platform,
        docker_client=docker_client,
    )

    if status_updates is None:
        logger.warning("Built image '%s' without any response", built_image_name)
        image = docker_client.images.get(str(effective_base_uri))
        return image, ImageURI.from_uri(f"{built_image_name}@{image.id}")

    error_update = rolling_print_status_updates(status_updates)
    if error_update is not None:
        logger.error(
            "Image build error details: '%s'", str(error_update.get("errorDetail"))
        )
        raise BuildError(
            f"Unable to build image '{built_image_name}': {error_update['error']}"
        )

    image = docker_client.images.get(built_image_name)
    return image, ImageURI.from_uri(f"{built_image_name}@{image.id}"), effective_base_uri


def _build_from_dockerfile(
    built_image_name: str,
    dockerfile_contents: str,
    platform: Optional[str],
    docker_client: docker.DockerClient,  # type: ignore
) -> Generator[Dict[str, Any], None, None]:
    """
    Builds a Docker image starting from Dockerfile contents.
    """
    optional_kwargs = dict()
    if platform is not None:
        optional_kwargs["platform"] = platform

    # the call to build below is blocking and takes a while
    # print a spinner in the meantime
    with stdout_spinner():
        # we have to create a tmp dockerfile and pass it instead of using the `fileobj`
        # option of the docker_client, because it does not work with contexts, so
        # operations like COPY do not work, as there exists no working dir context to copy
        # the targets from
        # API: https://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.build
        # Reported unresolved issue: https://github.com/docker/docker-py/issues/2105
        with tempfile.NamedTemporaryFile(mode="wt", delete=True) as dockerfile:
            dockerfile.write(dockerfile_contents)
            dockerfile.flush()

            status_updates = docker_client.api.build(
                dockerfile=dockerfile.name,
                # use the project root as the context
                path=os.getcwd(),
                tag=built_image_name,
                decode=True,
                pull=False,
                **optional_kwargs,
            )

    return status_updates


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

    # pip is always required to install the requirements file and/or sematic; see below
    logger.debug("Ensuring pip is present")
    pip_contents = _DOCKERFILE_ENSURE_PIP_TEMPLATE.format()
    dockerfile_contents = f"{dockerfile_contents}{pip_contents}"

    if source_build_config is not None and source_build_config.data is not None:
        logger.debug("Adding data files: %s", source_build_config.data)
        for data_glob in source_build_config.data:
            data_files = glob.glob(data_glob, recursive=True)
            if len(data_files) > 0:
                # sorting for determinism
                for data_file in sorted(data_files):
                    dockerfile_contents = (
                        f"{dockerfile_contents}\nCOPY {data_file} {data_file}"
                    )
        # provide an empty line between data and src, for readability
        dockerfile_contents = f"{dockerfile_contents}\n"

    if source_build_config is not None and source_build_config.requirements is not None:
        logger.debug("Adding requirements file: %s", source_build_config.requirements)
        requirements_contents = _DOCKERFILE_REQUIREMENTS_TEMPLATE.format(
            requirements_file=source_build_config.requirements
        )
        dockerfile_contents = f"{dockerfile_contents}{requirements_contents}"

    logger.debug("Ensuring Sematic is present")
    dockerfile_contents = f"{dockerfile_contents}{_DOCKERFILE_ENSURE_SEMATIC}"

    if (
        source_build_config is not None
        and source_build_config.src is not None
        and len(source_build_config.src) > 0
    ):
        logger.debug("Adding source files: %s", source_build_config.src)
        for src_glob in source_build_config.src:
            src_files = glob.glob(src_glob, recursive=True)
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

        logger.debug(
            f"Executing: executable={script_file} args={target} cwd={script_dir}"
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
        logger.info("Remote repo not configured; skipping image pushing")
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

    # the call to build below is blocking and takes a while
    # print a spinner in the meantime
    with stdout_spinner():
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

    error_update = rolling_print_status_updates(status_updates)
    if error_update is not None:
        logger.error(
            "Image push error details: '%s'", str(error_update.get("errorDetail"))
        )
        raise BuildError(f"Unable to push image: {error_update['error']}")

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
    repository, digest = image.attrs["RepoDigests"][0].split("@")
    # "RepoDigests" does not contain the fully qualified repo and tag;
    # we must use "RepoTags"
    # the repos here come in random order, but they all have the same tag
    _, tag = image.attrs["RepoTags"][0].split(":")

    return ImageURI(repository=repository, tag=tag, digest=digest)


def _get_local_image_name(target: str, build_config: BuildConfig) -> str:
    """
    Returns a local name to give to an image build for the specified target script,
    according to the specified build configuration.
    """
    dir_name = os.path.basename(os.path.dirname(os.path.abspath(target)))
    if dir_name == "/":
        dir_name = "default"

    if build_config.push is None:
        return f"{dir_name}:default"

    return f"{dir_name}:{build_config.push.get_tag()}"
