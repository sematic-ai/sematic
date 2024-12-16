# Standard Library
import time
from dataclasses import dataclass, replace

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import (
    mock_auth,  # noqa: F401
    mock_requests,  # noqa: F401
    mock_socketio,  # noqa: F401
    test_client,  # noqa: F401; noqa: F401
)
from sematic.db.db import DB
from sematic.db.models.artifact import Artifact
from sematic.db.models.external_resource import ExternalResource
from sematic.db.models.factories import make_artifact, make_user
from sematic.db.models.organization import Organization
from sematic.db.models.organization_user import OrganizationUser
from sematic.db.models.resolution import Resolution, ResolutionKind, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    count_jobs_by_run_id,
    count_runs,
    get_active_resolution_ids,
    get_artifact,
    get_external_resource_record,
    get_external_resources_by_run_id,
    get_job,
    get_jobs_by_run_id,
    get_orphaned_resource_records,
    get_orphaned_run_ids,
    get_resolution,
    get_resolution_ids_with_orphaned_jobs,
    get_resources_by_root_id,
    get_root_graph,
    get_run,
    get_run_graph,
    get_run_ids_with_orphaned_jobs,
    get_stale_resolution_ids,
    save_external_resource_record,
    save_graph,
    save_job,
    save_resolution,
    save_run,
    save_run_external_resource_links,
    save_user,
)
from sematic.db.tests.fixtures import (  # noqa: F401
    allow_any_run_state_transition,
    make_job,  # noqa: F811
    make_resolution,
    make_run,
    persisted_artifact,
    persisted_resolution,
    persisted_run,
    pg_mock,
    run,
    test_db,
)
from sematic.function import func
from sematic.plugins.abstract_external_resource import (
    AbstractExternalResource,
    ManagedBy,
    ResourceState,
)
from sematic.runners.local_runner import LocalRunner
from sematic.scheduling.job_details import (
    JobDetails,
    JobKind,
    JobStatus,
    KubernetesJobState,
)
from sematic.tests.fixtures import test_storage, valid_client_version  # noqa: F401
from sematic.utils.exceptions import IllegalStateTransitionError


def test_count_runs(test_db, run: Run):  # noqa: F811
    assert count_runs() == 0
    save_run(run)
    assert count_runs() == 1


def test_create_run(test_db, run: Run):  # noqa: F811
    assert run.created_at is None
    created_run = save_run(run)
    assert created_run == run
    assert run.created_at is not None
    assert run.updated_at is not None


def test_get_run(test_db, persisted_run: Run):  # noqa: F811
    fetched_run = get_run(persisted_run.id)

    assert fetched_run.id == persisted_run.id


def test_save_run(test_db, persisted_run: Run):  # noqa: F811
    persisted_run.name = "New Name"
    old_updated_at = persisted_run.updated_at
    save_run(persisted_run)
    fetched_run = get_run(persisted_run.id)
    assert fetched_run.name == "New Name"
    assert fetched_run.updated_at > old_updated_at


def test_get_resolution(test_db, persisted_resolution: Resolution):  # noqa: F811
    fetched_resolution = get_resolution(persisted_resolution.root_id)
    assert fetched_resolution.root_id == persisted_resolution.root_id
    assert fetched_resolution.status == persisted_resolution.status
    assert fetched_resolution.kind == persisted_resolution.kind
    assert (
        fetched_resolution.container_image_uris
        == persisted_resolution.container_image_uris
    )
    assert fetched_resolution.git_info == persisted_resolution.git_info
    assert fetched_resolution.settings_env_vars == persisted_resolution.settings_env_vars


def test_save_resolution(test_db, persisted_resolution: Resolution):  # noqa: F811
    assert persisted_resolution.status != ResolutionStatus.FAILED
    persisted_resolution.status = ResolutionStatus.FAILED
    save_resolution(persisted_resolution)
    fetched_resolution = get_resolution(persisted_resolution.root_id)
    assert fetched_resolution.status == ResolutionStatus.FAILED.value

    # multiple updates should be ok
    persisted_resolution.status = ResolutionStatus.COMPLETE
    save_resolution(persisted_resolution)
    fetched_resolution = get_resolution(persisted_resolution.root_id)
    assert fetched_resolution.status == ResolutionStatus.COMPLETE.value


def test_get_artifact(test_db, persisted_artifact: Artifact):  # noqa: F811
    artifact = get_artifact(persisted_artifact.id)

    assert artifact.id == persisted_artifact.id
    assert artifact.type_serialization == persisted_artifact.type_serialization
    assert artifact.json_summary == artifact.json_summary


def test_save_artifact(test_db):  # noqa: F811
    artifact, _ = make_artifact(42, int)
    save_graph(artifacts=[artifact], runs=[], edges=[])
    persisted_artifact = get_artifact(artifact.id)  # noqa: F811

    assert persisted_artifact.id == artifact.id
    assert persisted_artifact.type_serialization == artifact.type_serialization
    assert persisted_artifact.json_summary == artifact.json_summary
    assert persisted_artifact.created_at == artifact.created_at
    assert persisted_artifact.updated_at == artifact.updated_at


def test_update_artifact(test_db):  # noqa: F811
    original_artifact, _ = make_artifact(42, int)
    # create copies of these values, as sqlalchemy updates models in-place
    original_created_at = original_artifact.created_at
    original_updated_at = original_artifact.updated_at
    save_graph(artifacts=[original_artifact], runs=[], edges=[])

    updated_artifact, _ = make_artifact(42, int)
    assert updated_artifact.created_at != original_created_at

    save_graph(artifacts=[updated_artifact], runs=[], edges=[])

    persisted_artifact = get_artifact(original_artifact.id)  # noqa: F811

    assert persisted_artifact.id == original_artifact.id
    assert persisted_artifact.type_serialization == original_artifact.type_serialization
    assert persisted_artifact.json_summary == original_artifact.json_summary

    assert persisted_artifact.created_at == original_created_at
    assert persisted_artifact.updated_at == original_updated_at


def test_update_artifact_changed_content(test_db):  # noqa: F811
    original_artifact, _ = make_artifact(42, int)
    # create copies of these values, as sqlalchemy updates models in-place
    original_created_at = original_artifact.created_at
    original_updated_at = original_artifact.updated_at
    save_graph(artifacts=[original_artifact], runs=[], edges=[])

    updated_artifact, _ = make_artifact(42, int)

    # json of " 42" still deserializes to 42, but this change
    # helps us validate immutability
    updated_artifact.json_summary = f" {updated_artifact.json_summary}"

    with pytest.raises(
        ValueError, match="Artifact content change detected for field 'json_summary'"
    ):
        save_graph(artifacts=[updated_artifact], runs=[], edges=[])

    persisted_artifact = get_artifact(original_artifact.id)  # noqa: F811

    assert persisted_artifact.id == original_artifact.id
    assert persisted_artifact.type_serialization == original_artifact.type_serialization
    assert persisted_artifact.json_summary == original_artifact.json_summary

    assert persisted_artifact.created_at == original_created_at
    assert persisted_artifact.updated_at == original_updated_at


@func
def add(a: float, b: float) -> float:
    return a + b


@func
def pipeline(a: float, b: float) -> float:
    return add(add(a, b), b)


@pytest.mark.parametrize(
    "fn, run_count, artifact_count, edge_count",
    ((get_run_graph, 1, 3, 3), (get_root_graph, 3, 4, 8)),
)
def test_get_run_graph(
    mock_auth,  # noqa: F811
    mock_socketio,  # noqa: F811
    fn,
    run_count: int,
    artifact_count: int,
    edge_count: int,
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    future = pipeline(1, 2)
    LocalRunner().run(future)

    runs, artifacts, edges = fn(future.id)

    assert len(runs) == run_count
    assert len(artifacts) == artifact_count
    assert len(edges) == edge_count


@dataclass(frozen=True)
class SomeResource(AbstractExternalResource):
    some_field: int = 0


def test_save_external_resource_record(test_db):  # noqa: F811
    resource1 = SomeResource(some_field=42)
    record1 = ExternalResource.from_resource(resource1)
    save_external_resource_record(record1)
    saved_record1 = get_external_resource_record(record1.id)

    assert saved_record1.updated_at is not None
    assert saved_record1.created_at is not None
    assert saved_record1.resource_state == resource1.status.state

    resource2 = replace(
        resource1,
        status=replace(
            resource1.status,
            state=ResourceState.ACTIVATING,
            message="Activating",
            managed_by=ManagedBy.SERVER,
        ),
    )
    record2 = ExternalResource.from_resource(resource2)
    save_external_resource_record(record2)
    saved_record2 = get_external_resource_record(record2.id)
    assert saved_record2.history == (resource2, resource1)
    assert saved_record2.updated_at is not None
    assert saved_record2.created_at is not None
    assert saved_record2.updated_at > saved_record1.updated_at
    assert saved_record2.created_at == saved_record1.created_at

    resource3 = replace(
        resource2,
        status=replace(
            resource2.status,
            last_update_epoch_time=resource2.status.last_update_epoch_time + 1,
        ),
    )
    record3 = ExternalResource.from_resource(resource3)
    saved_record3 = save_external_resource_record(record3)
    assert (
        saved_record3.last_updated_epoch_seconds
        == resource3.status.last_update_epoch_time
    )

    # history is not updated when the object is unchanged except for
    # timestamp
    assert saved_record3.history == (resource2, resource1)

    resource4 = replace(
        resource3,
        status=replace(
            resource3.status,
            last_update_epoch_time=resource3.status.last_update_epoch_time + 1,
        ),
        some_field=43,
    )
    record4 = ExternalResource.from_resource(resource4)
    saved_record4 = save_external_resource_record(record4)

    # history is updated for changes in other fields
    assert saved_record4.history == (resource4, resource2, resource1)

    resource5 = replace(
        resource4,
        status=replace(
            resource4.status,
            state=ResourceState.CREATED,
        ),
    )
    record5 = ExternalResource.from_resource(resource5)
    with pytest.raises(IllegalStateTransitionError):
        save_external_resource_record(record5)


def test_run_resource_links(test_db):  # noqa: F811
    root_run = make_run()
    child_run_1 = make_run(root_id=root_run.id)
    child_run_2 = make_run(root_id=root_run.id)
    child_run_3 = make_run(root_id=root_run.id)
    other_root_run = make_run()
    for r in [root_run, child_run_1, child_run_2, child_run_3, other_root_run]:
        save_run(r)

    resource_1 = SomeResource(some_field=1)
    resource_2 = SomeResource(some_field=2)
    resource_3 = SomeResource(some_field=3)
    resource_4 = SomeResource(some_field=4)

    for resource in [resource_1, resource_2, resource_3, resource_4]:
        save_external_resource_record(ExternalResource.from_resource(resource))

    save_run_external_resource_links([resource_1.id], child_run_1.id)
    save_run_external_resource_links([resource_2.id], child_run_2.id)

    # multiple resources linked with one run
    save_run_external_resource_links([resource_3.id], child_run_2.id)

    save_run_external_resource_links([resource_4.id], other_root_run.id)

    resources = get_resources_by_root_id(root_run.id)
    assert len(resources) == 3
    assert all(isinstance(record, ExternalResource) for record in resources)
    resource_ids = {resource.id for resource in resources}
    assert resource_ids == {resource_1.id, resource_2.id, resource_3.id}


def test_get_stale_resolution_ids(
    test_db,  # noqa: F811
    allow_any_run_state_transition,  # noqa: F811
):
    # Stale because run is dead and resolution isn't
    root_run_1 = make_run(future_state=FutureState.CANCELED)
    resolution_1 = make_resolution(root_id=root_run_1.id, status=ResolutionStatus.RUNNING)

    # not stale because resolution and run are alive
    root_run_2 = make_run(future_state=FutureState.SCHEDULED)
    resolution_2 = make_resolution(root_id=root_run_2.id, status=ResolutionStatus.RUNNING)

    # not stale because neither resolution nor run are alive
    root_run_3 = make_run(future_state=FutureState.CANCELED)
    resolution_3 = make_resolution(
        root_id=root_run_3.id, status=ResolutionStatus.CANCELED
    )

    for run in [root_run_1, root_run_2, root_run_3]:  # noqa: F402
        save_run(run)

    for resolution in [resolution_1, resolution_2, resolution_3]:
        save_resolution(resolution)

    stale_resolution_ids = get_stale_resolution_ids()
    assert stale_resolution_ids == [resolution_1.root_id]


def test_get_orphaned_run_ids(test_db, allow_any_run_state_transition):  # noqa: F811
    # Runs are orphaned because resolution is terminal but runs aren't
    root_run_1 = make_run(future_state=FutureState.RAN)
    child_run_1 = make_run(root_id=root_run_1.id, future_state=FutureState.SCHEDULED)
    resolution_1 = make_resolution(
        root_id=root_run_1.id, status=ResolutionStatus.CANCELED
    )

    # Not orphaned because everything is still alive
    root_run_2 = make_run(future_state=FutureState.SCHEDULED)
    child_run_2 = make_run(root_id=root_run_2.id, future_state=FutureState.RAN)
    resolution_2 = make_resolution(root_id=root_run_2.id, status=ResolutionStatus.RUNNING)

    # Root run is terminal and therefore not orphaned. Child run is alive but resolution
    # is not--therefore child is orphaned.
    root_run_3 = make_run(future_state=FutureState.CANCELED)
    child_run_3 = make_run(root_id=root_run_3.id, future_state=FutureState.RAN)
    resolution_3 = make_resolution(
        root_id=root_run_3.id, status=ResolutionStatus.CANCELED
    )

    for run in [  # noqa: F402
        root_run_1,
        child_run_1,
        root_run_2,
        child_run_2,
        root_run_3,
        child_run_3,
    ]:
        save_run(run)

    for resolution in [resolution_1, resolution_2, resolution_3]:
        save_resolution(resolution)

    orphaned_run_ids = get_orphaned_run_ids()
    assert set(orphaned_run_ids) == {root_run_1.id, child_run_1.id, child_run_3.id}


def test_get_orphaned_resource_records(test_db):  # noqa: F811
    root_run = make_run()
    resolution = make_resolution(root_id=root_run.id, status=ResolutionStatus.CANCELED)
    save_resolution(resolution)

    child_run_1 = make_run(root_id=root_run.id)
    child_run_2 = make_run(root_id=root_run.id)
    child_run_3 = make_run(root_id=root_run.id)

    other_root_run = make_run()
    other_resolution = make_resolution(root_id=other_root_run.id)
    save_resolution(other_resolution)
    for r in [root_run, child_run_1, child_run_2, child_run_3, other_root_run]:
        save_run(r)

    resource_1 = SomeResource(some_field=1)
    resource_2 = SomeResource(some_field=2)
    resource_3 = SomeResource(some_field=3)
    resource_4 = SomeResource(some_field=4)

    for resource in [resource_1, resource_2, resource_3, resource_4]:
        save_external_resource_record(ExternalResource.from_resource(resource))

    save_run_external_resource_links([resource_1.id], child_run_1.id)
    save_run_external_resource_links([resource_2.id], child_run_2.id)

    # multiple resources linked with one run
    save_run_external_resource_links([resource_3.id], child_run_2.id)

    save_run_external_resource_links([resource_4.id], other_root_run.id)

    orphan_ids = [resource.id for resource in get_orphaned_resource_records()]
    assert set(orphan_ids) == {resource_1.id, resource_2.id, resource_3.id}


def test_get_external_resources_by_run_id(test_db):  # noqa: F811
    root_run = make_run()
    child_run_1 = make_run(root_id=root_run.id)
    other_root_run = make_run()
    for r in [root_run, child_run_1, other_root_run]:
        save_run(r)

    resource_1 = SomeResource(some_field=1)
    resource_2 = SomeResource(some_field=2)
    resource_3 = SomeResource(some_field=3)

    for resource in [resource_1, resource_2, resource_3]:
        save_external_resource_record(ExternalResource.from_resource(resource))

    # multiple resources linked with one run
    save_run_external_resource_links([resource_1.id], child_run_1.id)
    save_run_external_resource_links([resource_2.id], child_run_1.id)
    save_run_external_resource_links([resource_3.id], other_root_run.id)

    resources = get_external_resources_by_run_id(child_run_1.id)
    assert len(resources) == 2
    assert all(isinstance(record, ExternalResource) for record in resources)
    resource_ids = {resource.id for resource in resources}
    assert resource_ids == {resource_1.id, resource_2.id}


def test_fail_invalid_run_state_transition(test_db):  # noqa: F811
    run = make_run(future_state=FutureState.CREATED)  # noqa: F811
    save_run(run)

    run.future_state = FutureState.RESOLVED
    with pytest.raises(IllegalStateTransitionError):
        save_run(run)


def test_save_read_jobs(test_db):  # noqa: F811
    root_run = make_run()
    child_run = make_run(root_id=root_run.id)
    for r in [root_run, child_run]:
        save_run(r)

    status = JobStatus(
        state=KubernetesJobState.Requested,
        message="Just created",
        last_updated_epoch_seconds=time.time(),
    )
    details = JobDetails(try_number=0)
    job = make_job(details=details, status=status, run_id=child_run.id)
    save_job(job)

    details.has_started = True
    status = replace(
        status,
        state=KubernetesJobState.Running,
        last_updated_epoch_seconds=status.last_updated_epoch_seconds + 0.1,
    )
    job.update_status(status)
    save_job(job)
    status_history = get_job(job.name, job.namespace).status_history
    assert len(status_history) == 2

    assert get_jobs_by_run_id(root_run.id) == []
    assert count_jobs_by_run_id(child_run.id) == 1

    status = JobStatus(
        state=KubernetesJobState.Requested,
        message="Just created",
        last_updated_epoch_seconds=time.time(),
    )

    retry_details = replace(
        details,
        try_number=1,
    )
    retry_job = make_job(
        name="foo-1",
        run_id=child_run.id,
        status=status,
        details=retry_details,
    )

    save_job(retry_job)
    assert count_jobs_by_run_id(child_run.id) == 2

    retry_job_from_scratch = make_job(
        name="foo-1",
        run_id=child_run.id,
        status=replace(
            status,
            last_updated_epoch_seconds=(
                retry_job.latest_status.last_updated_epoch_seconds - 0.1
            ),
        ),
        details=retry_details,
    )

    with pytest.raises(
        IllegalStateTransitionError,
        match=r"Tried to update status from .* to .*, but the latter was older",
    ):
        save_job(retry_job_from_scratch)


def test_get_run_ids_with_orphaned_jobs(test_db):  # noqa: F811
    root_run = make_run()
    child_run_1 = make_run(root_id=root_run.id)
    child_run_2 = make_run(root_id=root_run.id)
    for r in [root_run, child_run_1, child_run_2]:
        save_run(r)

    created_status = JobStatus(
        state=KubernetesJobState.Requested,
        message="Just created",
        last_updated_epoch_seconds=time.time(),
    )

    details_1 = JobDetails(try_number=0)
    job_1 = make_job(
        details=details_1, name="job_1", status=created_status, run_id=child_run_1.id
    )
    save_job(job_1)

    details_2 = JobDetails(try_number=0)
    job_2 = make_job(
        details=details_2, name="job_2", status=created_status, run_id=child_run_2.id
    )
    save_job(job_2)

    child_run_2.future_state = FutureState.SCHEDULED
    save_run(child_run_2)
    child_run_2.future_state = FutureState.RESOLVED
    save_run(child_run_2)

    run_ids = get_run_ids_with_orphaned_jobs()
    assert run_ids == [child_run_2.id]


def test_get_resolution_ids_with_orphaned_jobs(test_db):  # noqa: F811
    root_run_1 = make_run()
    root_run_2 = make_run()
    save_run(root_run_1)
    save_run(root_run_2)

    resolution_1 = make_resolution(root_id=root_run_1.id)
    resolution_2 = make_resolution(root_id=root_run_2.id, status=ResolutionStatus.FAILED)
    save_resolution(resolution_1)
    save_resolution(resolution_2)

    created_status = JobStatus(
        state=KubernetesJobState.Requested,
        message="Just created",
        last_updated_epoch_seconds=time.time(),
    )

    details_1 = JobDetails(try_number=0)
    job_1 = make_job(
        details=details_1,
        name="job_1",
        status=created_status,
        run_id=resolution_1.root_id,
        kind=JobKind.resolver,
    )
    save_job(job_1)

    details_2 = JobDetails(try_number=0)
    job_2 = make_job(
        details=details_2,
        name="job_2",
        status=created_status,
        run_id=resolution_2.root_id,
        kind=JobKind.resolver,
    )
    save_job(job_2)

    resolution_ids = get_resolution_ids_with_orphaned_jobs()
    assert resolution_ids == [resolution_2.root_id]


def test_save_user(
    test_db: DB,  # noqa: F811
):
    # save the first user
    user1 = make_user(
        email="elvis@graceland.com",
        first_name="Elvis",
        last_name="Presley",
        avatar_url="https://?:",
    )
    save_user(user1)

    with test_db.get_session() as session:
        users = session.query(User).all()
        assert len(users) == 1
        assert users[0].id is not None
        assert users[0].email == "elvis@graceland.com"
        assert users[0].first_name == "Elvis"
        assert users[0].last_name == "Presley"
        assert users[0].avatar_url == "https://?:"
        assert users[0].api_key is not None

        organizations = session.query(Organization).all()
        assert len(organizations) == 1
        assert organizations[0].id == users[0].id
        assert organizations[0].name == "Elvis Presley"
        assert organizations[0].kubernetes_namespace is None

        organizations_users = session.query(OrganizationUser).all()
        assert len(organizations_users) == 1
        assert organizations_users[0].organization_id == organizations[0].id
        assert organizations_users[0].user_id == users[0].id
        assert organizations_users[0].admin is True

    # save the second user
    user2 = make_user(
        email="michael@wonderland.com",
        first_name="Michael",
        last_name="Jackson",
        avatar_url="https://B)",
    )
    save_user(user2)

    with test_db.get_session() as session:
        users = session.query(User).all()
        assert len(users) == 2
        assert users[1].id is not None
        assert users[1].email == "michael@wonderland.com"
        assert users[1].first_name == "Michael"
        assert users[1].last_name == "Jackson"
        assert users[1].avatar_url == "https://B)"
        assert users[1].api_key is not None

        organizations = session.query(Organization).all()
        assert len(organizations) == 2
        assert organizations[1].id == users[1].id
        assert organizations[1].name == "Michael Jackson"
        assert organizations[1].kubernetes_namespace is None

        organizations_users = session.query(OrganizationUser).all()
        assert len(organizations_users) == 2
        assert organizations_users[1].organization_id == organizations[1].id
        assert organizations_users[1].user_id == users[1].id
        assert organizations_users[1].admin is True

    # save the first user again
    save_user(user1)

    with test_db.get_session() as session:
        users = session.query(User).all()
        assert len(users) == 2

        organizations = session.query(Organization).all()
        assert len(organizations) == 2

        organizations_users = session.query(OrganizationUser).all()
        assert len(organizations_users) == 2


def test_get_active_resolution_ids(
    test_db,  # noqa: F811
    allow_any_run_state_transition,  # noqa: F811
):
    root_run_1 = make_run(future_state=FutureState.SCHEDULED)
    resolution_1 = make_resolution(root_id=root_run_1.id, status=ResolutionStatus.RUNNING)

    root_run_2 = make_run(future_state=FutureState.CREATED)
    resolution_2 = make_resolution(root_id=root_run_2.id, status=ResolutionStatus.CREATED)

    root_run_3 = make_run(future_state=FutureState.RESOLVED)
    resolution_3 = make_resolution(
        root_id=root_run_3.id, status=ResolutionStatus.COMPLETE
    )

    root_run_4 = make_run(future_state=FutureState.SCHEDULED)
    resolution_4 = make_resolution(
        root_id=root_run_4.id,
        status=ResolutionStatus.RUNNING,
        kind=ResolutionKind.LOCAL,
    )

    for run in [root_run_1, root_run_2, root_run_3, root_run_4]:  # noqa: F402
        save_run(run)

    for resolution in [resolution_1, resolution_2, resolution_3, resolution_4]:
        save_resolution(resolution)

    active_resolution_ids = get_active_resolution_ids(ResolutionKind.KUBERNETES)
    assert set(active_resolution_ids) == {resolution_1.root_id, resolution_2.root_id}
