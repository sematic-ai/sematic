# Glow
import pytest
from glow.db.models.run import Run
from glow.abstract_future import FutureState


def test_set_future_state():
    run = Run()
    run.future_state = FutureState.CREATED
    assert run.future_state == FutureState.CREATED.value


def test_set_future_fail():
    with pytest.raises(ValueError, match="future_state must be a FutureState"):
        Run(future_state=FutureState.CREATED.value)


def test_set_description():
    run = Run(description="   abc\n   ")
    assert run.description == "abc"
