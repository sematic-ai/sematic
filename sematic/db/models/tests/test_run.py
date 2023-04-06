# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.run import Run


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
