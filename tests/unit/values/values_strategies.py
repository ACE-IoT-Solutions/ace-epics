"""Synthetic representable value trees for Clause 4 grammar property testing."""

from decimal import Decimal

from hypothesis import strategies as st

from ace_epics.model.names import NamedToken
from ace_epics.values.nodes import (
    BooleanValue,
    CharacterStringValue,
    ContextTaggedValue,
    DateRangeValue,
    DateValue,
    EmptyElement,
    EnumeratedValue,
    GroupValue,
    IntegerValue,
    NullValue,
    ObjectIdentifierValue,
    OctetStringValue,
    RealValue,
    TimeValue,
    UnspecifiedValue,
    WildcardValue,
)


def value_nodes():
    names = st.sampled_from(["analog-input", "active", "no-fault-detected", "kilowatts", "device"])
    date = st.builds(
        DateValue,
        weekday=st.one_of(st.none(), st.integers(1, 7), st.just(WildcardValue())),
        day=st.one_of(st.integers(1, 28), st.just(WildcardValue())),
        month=st.one_of(st.integers(1, 12), st.just(WildcardValue())),
        year=st.one_of(st.integers(1900, 2200), st.just(WildcardValue())),
    )

    def field(limit):
        return st.one_of(st.integers(0, limit), st.just(WildcardValue()))

    primitive = st.one_of(
        st.just(NullValue()),
        st.builds(BooleanValue, value=st.booleans(), short=st.booleans()),
        st.builds(IntegerValue, value=st.integers(-(2**32), 2**32)),
        st.integers(-100000, 100000).map(
            lambda v: RealValue(value=Decimal(v) / 100, text=f"{Decimal(v) / 100:.2f}")
        ),
        st.builds(OctetStringValue, value=st.binary(max_size=16)),
        st.builds(CharacterStringValue, value=st.text(alphabet="abcXYZ012 --,()<>é", max_size=20)),
        names.map(lambda n: EnumeratedValue(name=NamedToken(canonical=n))),
        st.integers(128, 1023).map(
            lambda n: EnumeratedValue(
                name=NamedToken(canonical=f"proprietary-object-type-{n}"), proprietary_number=n
            )
        ),
        date,
        st.builds(DateRangeValue, start=date, end=date),
        st.builds(
            TimeValue, hour=field(23), minute=field(59), second=field(59), hundredth=field(99)
        ),
        st.builds(
            ObjectIdentifierValue,
            object_type=st.one_of(
                names.map(lambda n: NamedToken(canonical=n)), st.integers(128, 1023)
            ),
            instance=st.integers(0, 4194302),
        ),
        st.just(UnspecifiedValue()),
        st.just(WildcardValue()),
    )
    return st.recursive(
        primitive,
        lambda children: st.one_of(
            st.builds(
                GroupValue,
                delimiter=st.just("{"),
                elements=st.lists(st.one_of(children, st.just(EmptyElement())), max_size=5),
            ),
            st.builds(ContextTaggedValue, tag=st.integers(0, 255), value=children),
        ),
        max_leaves=20,
    )
