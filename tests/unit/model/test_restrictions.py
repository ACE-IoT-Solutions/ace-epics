import pytest
from pydantic import ValidationError

from ace_epics.model.restrictions import DefaultRestrictions, Restrictions, merge
from ace_epics.values import DateValue, IntegerValue, RealValue


def test_merge_preserves_datatypes_and_only_overrides_defined_fields():
    default = Restrictions(minimum=IntegerValue(value=-10), maximum=IntegerValue(value=10))
    override = Restrictions(maximum=RealValue(value="20.0"), resolution=RealValue(value="0.1"))
    result = merge(default, override)
    assert result.minimum == default.minimum
    assert result.maximum == override.maximum
    assert result.resolution == override.resolution
    assert merge(None, None) == Restrictions()
    assert merge(default, None) == default
    assert merge(None, override) == override
    date = DateValue(day=1, month=1, year=2024)
    assert Restrictions(minimum=date).minimum == date


def test_lengths_and_named_allowed_values():
    restrictions = Restrictions(
        **{"maximum length string": 30, "allowed values": ["milliamperes", "Amperes"]}
    )
    assert restrictions.allowed_values is not None
    assert restrictions.allowed_values[1].canonical == "amperes"
    for value in [-1, 5.5]:
        with pytest.raises(ValidationError):
            Restrictions(maximum_length_string=value)


def test_default_restrictions_warn_without_rejecting():
    assert not DefaultRestrictions(real=Restrictions(minimum=RealValue(value="0.0"))).warnings()
    defaults = DefaultRestrictions(
        octet_string=Restrictions(maximum_length_list=5),
        extra={"time": Restrictions(resolution=IntegerValue(value=1))},
    )
    assert defaults.warnings()[0].code == "M-DEFAULT-RESTRICTION"
    assert isinstance(defaults.extra["time"].resolution, IntegerValue)
    assert defaults.extra["time"].resolution.value == 1
