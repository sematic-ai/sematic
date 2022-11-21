# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.run import Run
from sematic.scheduling.external_job import ExternalJob


def test_set_future_state():
    run = Run()
    run.future_state = FutureState.CREATED
    assert run.future_state == FutureState.CREATED.value


def test_set_description():
    run = Run(description="   abc\n   ")
    assert run.description == "abc"


def test_description_format_indended_spaces():
    run = Run(description="   line1\n\n    line2")
    assert run.description == "line1\n\nline2"


def test_description_format_remove_tab():
    run = Run(description="   line1\n\n\tline2")
    assert run.description == "line1\n\nline2"


def test_external_jobs():
    run = Run()
    assert run.external_jobs_json is None
    job_1 = ExternalJob(kind="k8s", try_number=0, external_job_id="foo-0")
    job_2 = ExternalJob(kind="k8s", try_number=1, external_job_id="foo-1")
    run.external_jobs = [job_1, job_2]
    assert run.external_jobs == (job_1, job_2)
    assert run.external_jobs_json is not None
