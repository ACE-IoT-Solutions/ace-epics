import re

import pytest
from pydantic import TypeAdapter, ValidationError

from ace_epics.model.datalink import (
    Arcnet,
    BacnetIp,
    BacnetIpv6,
    BacnetSc,
    DataLinkOption,
    Iso8802_3,
    MsTp,
    Other,
    PointToPoint,
    Zigbee,
)

OPTIONS = [
    *[
        Iso8802_3.model_validate({"media": media})
        for media in ["10BASE5", "10BASE2", "10BASET", "fiber"]
    ],
    *[
        Arcnet.model_validate({"media": media})
        for media in [
            "coax star",
            "coax bus",
            "twisted pair star",
            "twisted pair bus",
            "fiber star",
        ]
    ],
    Arcnet(media="twisted pair, EIA-485", baud_rates=[9600, 19200]),
    MsTp(role="manager", baud_rates=[9600, 19200, 38400]),
    MsTp(role="subordinate", baud_rates=[9600]),
    PointToPoint(medium="EIA 232", baud_rates=[9600]),
    PointToPoint(medium="Modem", baud_rates=[9600, 19200]),
    PointToPoint(medium="Modem", autobaud=(9600, 57600)),
    BacnetIp(variant="'DIX' Ethernet"),
    BacnetIp(variant="Other"),
    BacnetIpv6(),
    BacnetSc(),
    Zigbee(),
    Other(),
    Other(text="custom transport"),
]


@pytest.mark.parametrize("option", OPTIONS)
def test_every_literal_roundtrips_regex_and_union(option):
    match = re.fullmatch(option.regex, option.canonical_text())
    assert match
    arguments = {k: v for k, v in match.groupdict().items() if v is not None}
    if "baud_rates" in arguments:
        arguments["baud_rates"] = [int(n) for n in arguments["baud_rates"].split(", ")]
    if "low" in arguments:
        arguments["autobaud"] = (int(arguments.pop("low")), int(arguments.pop("high")))
    assert type(option)(**arguments) == option
    assert TypeAdapter(DataLinkOption).validate_json(option.model_dump_json()) == option


@pytest.mark.parametrize(
    "factory,args",
    [
        (Arcnet, {"media": "twisted pair, EIA-485"}),
        (Arcnet, {"media": "fiber star", "baud_rates": [9600]}),
        (Arcnet, {"media": "fiber bus"}),
        (MsTp, {"role": "manager", "baud_rates": []}),
        (PointToPoint, {"medium": "Modem"}),
        (PointToPoint, {"medium": "Modem", "baud_rates": [9600], "autobaud": (9600, 19200)}),
        (PointToPoint, {"medium": "EIA 232", "autobaud": (9600, 19200)}),
        (PointToPoint, {"medium": "Modem", "autobaud": (19200, 9600)}),
        (BacnetIpv6, {"variant": "Other"}),
    ],
)
def test_invalid_parameters(factory, args):
    with pytest.raises(ValidationError):
        factory(**args)


def test_mstp_9600_advisory():
    assert not MsTp(role="manager", baud_rates=[9600]).warnings()
    assert MsTp(role="manager", baud_rates=[19200]).warnings()[0].code == "M-MSTP-9600"
