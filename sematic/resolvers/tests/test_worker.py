# Standard Library
import datetime
import os
import sys
import tempfile
import uuid
from typing import List
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic import api_client
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_auth,
    mock_requests,
    mock_socketio,
    test_client,
)
from sematic.calculator import func
from sematic.config.tests.fixtures import mock_settings
from sematic.config.user_settings import UserSettingsVar
from sematic.db.models.edge import Edge
from sematic.db.models.factories import make_artifact, make_run_from_future
from sematic.db.models.resolution import ResolutionStatus
from sematic.db.queries import (
    get_resolution,
    get_root_graph,
    save_graph,
    save_resolution,
)
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.future_context import PrivateContext, SematicContext
from sematic.resolvers.cloud_resolver import CloudResolver
from sematic.resolvers.worker import _emulate_interpreter, main, wrap_main_with_logging
from sematic.tests.fixtures import (  # noqa: F401
    environment_variables,
    test_storage,
    valid_client_version,
)
from sematic.utils.stdout import redirect_to_file


@func
def add(a: float, b: float) -> float:
    return a + b


@func
def pipeline(a: float, b: float) -> float:
    return add(a, b)


@mock.patch(
    "sematic.resolvers.cloud_resolver.get_image_uris", return_value=dict(default="foo")
)
@mock.patch("sematic.resolvers.silent_resolver.set_context")
@mock.patch("sematic.api_client.schedule_resolution")
@mock.patch("kubernetes.config.load_kube_config")
def test_main(
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_job: mock.MagicMock,
    mock_set_context: mock.MagicMock,
    mock_get_image: mock.MagicMock,
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    mock_requests,  # noqa: F811
    test_db,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    # On the user's machine
    resolver = CloudResolver(detach=True)

    future = pipeline(1, 2)

    future.resolve(resolver)
    resolution = get_resolution(future.id)
    resolution.status = ResolutionStatus.SCHEDULED
    save_resolution(resolution)

    # In the driver job

    main(run_id=future.id, resolve=True)

    runs, artifacts, edges = get_root_graph(future.id)
    assert len(runs) == 2
    assert len(artifacts) == 3
    assert len(edges) == 6
    mock_set_context.assert_any_call(
        SematicContext(
            run_id=future.id,
            root_id=future.id,
            private=PrivateContext(
                resolver_class_path=CloudResolver.classpath(),
            ),
        )
    )


@mock.patch(
    "sematic.resolvers.cloud_resolver.get_image_uris", return_value=dict(default="foo")
)
@mock.patch("sematic.resolvers.worker.set_context")
@mock.patch("sematic.api_client.schedule_resolution")
@mock.patch("kubernetes.config.load_kube_config")
def test_main_func(
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_job: mock.MagicMock,
    mock_set_context: mock.MagicMock,
    mock_get_image: mock.MagicMock,
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    mock_requests,  # noqa: F811
    test_db,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    future = add(1, 1)
    artifact_1, payload_1 = make_artifact(1, int)
    artifact_2, payload_2 = make_artifact(1, int)

    api_client.store_payloads(payload_1 + payload_2)

    edge_1 = Edge(
        id=uuid.uuid4().hex,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
        source_run_id=None,
        destination_run_id=future.id,
        destination_name="a",
        artifact_id=artifact_1.id,
        parent_id=None,
    )
    edge_2 = Edge(
        id=uuid.uuid4().hex,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
        source_run_id=None,
        destination_run_id=future.id,
        destination_name="b",
        artifact_id=artifact_2.id,
        parent_id=None,
    )

    out_edge = Edge(
        id=uuid.uuid4().hex,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
        source_run_id=future.id,
        destination_run_id=None,
        destination_name=None,
        artifact_id=None,
        parent_id=None,
    )
    run = make_run_from_future(future)
    run.root_id = run.id
    save_graph(
        runs=[run], artifacts=[artifact_1, artifact_2], edges=[edge_1, edge_2, out_edge]
    )

    # on the worker
    main(run_id=future.id, resolve=False)

    runs, artifacts, _ = get_root_graph(future.id)
    assert len(runs) == 1
    output_artifact_id = [
        artifact.id
        for artifact in artifacts
        if artifact.id not in (artifact_1.id, artifact_2.id)
    ][0]
    value = api_client.get_artifact_value_by_id(output_artifact_id)
    assert value == 2  # 1+1==2. Rest assured that math is intact!

    mock_set_context.assert_called_once_with(
        SematicContext(
            run_id=future.id,
            root_id=future.id,
            private=PrivateContext(
                resolver_class_path=CloudResolver.classpath(),
            ),
        )
    )


@func
def fail():
    raise Exception("FAIL!")


@mock.patch(
    "sematic.resolvers.cloud_resolver.get_image_uris", return_value=dict(default="foo")
)
@mock.patch("sematic.api_client.schedule_resolution")
@mock.patch("kubernetes.config.load_kube_config")
def test_fail(
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_job: mock.MagicMock,
    mock_get_image: mock.MagicMock,
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    # On the user's machine
    resolver = CloudResolver(detach=True)

    future = fail()

    future.resolve(resolver)
    resolution = get_resolution(future.id)
    resolution.status = ResolutionStatus.SCHEDULED
    save_resolution(resolution)

    # In the driver job
    with pytest.raises(Exception, match="FAIL!"):
        main(run_id=future.id, resolve=True)

    runs, _, _ = get_root_graph(future.id)

    assert runs[0].future_state == FutureState.FAILED.value
    assert runs[0].exception_metadata is not None
    assert "FAIL!" in runs[0].exception_metadata.repr


def test_emulate_interpreter():
    # if the sematic import failed, we wouldn't reach the sys.exit, and we'd
    # get a different exit code.
    exit_code = _emulate_interpreter(
        [sys.executable, "-c", "import sematic; import sys; sys.exit(42)"]
    )
    assert exit_code == 42


class MockLogIngestor:
    def __init__(self) -> None:
        self._tempfile_path = None
        self._redirection_context = None
        self.logs: List[str] = []

    def __enter__(self, *args, **kwargs):
        self._tempfile_path = tempfile.NamedTemporaryFile(mode="w+", delete=False).name
        self._redirection_context = redirect_to_file(self._tempfile_path)
        return self._redirection_context.__enter__()

    def __exit__(self, *args, **kwargs):
        with open(self._tempfile_path, "r") as fp:
            self.logs = [line.strip() for line in fp]
        os.remove(self._tempfile_path)
        self._redirection_context.__exit__(*args, **kwargs)
        self._tempfile_path = None
        self._redirection_context = None


@mock.patch(f"{main.__module__}.parse_args")
@mock.patch(f"{main.__module__}.ingested_logs")
@mock.patch(f"{main.__module__}.{main.__name__}")
def test_wrap_main_with_logging(mock_main, mock_ingested_logs, mock_parse_args):
    mock_ingestor = MockLogIngestor()
    mock_ingested_logs.return_value = mock_ingestor

    logs_from_main = "Hello from main"
    mock_main.side_effect = lambda *args, **kwargs: print(logs_from_main)

    with mock_settings(None):
        with environment_variables(
            {UserSettingsVar.SEMATIC_LOG_INGESTION_MODE.value: "off"}
        ):
            wrap_main_with_logging()
    assert logs_from_main not in mock_ingestor.logs

    # Check the message about ingestion being disabled
    assert any("disabled" in line for line in mock_ingestor.logs)
    assert any(
        UserSettingsVar.SEMATIC_LOG_INGESTION_MODE.value in line
        for line in mock_ingestor.logs
    )

    with mock_settings(None):
        wrap_main_with_logging()
    assert logs_from_main in mock_ingestor.logs
