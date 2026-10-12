import pytest
from pydantic import ValidationError

from ace_epics.model.timers import TIMER_ALIASES, FailTimes


@pytest.mark.parametrize("alias,field", TIMER_ALIASES.items())
def test_clause_six_aliases(alias, field):
    assert getattr(FailTimes.model_validate({alias: 1.5}), field) == 1.5


@pytest.mark.parametrize("field", [name for name in FailTimes.model_fields if name != "extra"])
def test_all_fourteen_timer_fields(field):
    assert getattr(FailTimes.model_validate({field: 0.0}), field) == 0.0
    with pytest.raises(ValidationError):
        FailTimes.model_validate({field: -0.1})


def test_extra_and_partial_timers():
    assert FailTimes().notification_fail_time is None
    assert FailTimes(extra={"Custom": 2.5}).extra == {"Custom": 2.5}
    for value in [-1, float("nan"), float("inf")]:
        with pytest.raises(ValidationError):
            FailTimes(extra={"Custom": value})
