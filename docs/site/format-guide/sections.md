# EPICS sections and model traceability

All document models reject unknown fields, preserve string content, and accept snake_case names or the printed keyword aliases. Warnings are collected in `EpicsDocument.diagnostics` and excluded from serialization. Models perform no file I/O and use no BACnet knowledge provider.

## Header (4.1)

`PICS 0` selects UTF-8. `PicsHeader.charset_code` accepts all six selectors: 0 UTF-8, 1 DBCS, 2 JIS X 0208, 3 UCS-4, 4 UCS-2, and 5 ISO 8859-1. `charset.octet_width` reports the header code-unit width.

## General information (4.5.1)

```text
Vendor Name: "Synthetic vendor"
Product Name: "Example"
Product Model Number: "Model 1"
Product Description: "Test equipment"
```

`GeneralInformation` has the four corresponding snake_case fields. These strings have no model-imposed length limit.

## BIBBs (4.5.2)

```text
BIBBs Supported: { DS-RP-B DM-DDB-A }
```

`Bibb` stores a normalized name and original spelling. Unexpected Annex K name patterns and duplicate declarations produce warnings.

## Services (4.5.3)

```text
BACnet Standard Application Services Supported: { Who-Is Initiate Execute }
```

`ServiceSupport` has `name`, `initiate`, and `execute`; at least one direction is required.

## Object types (4.5.4)

```text
Standard Object Types Supported: { Analog Value Createable Deleteable }
```

`ObjectTypeSupport` has `name`, `createable`, and `deleteable`. `Creatable` is an input alias; serialization emits `Createable`.

## Data links (4.5.5)

```text
Data Link Layer Option: { MS/TP manager. Baud rate(s): 9600, 19200 }
```

`DataLinkOption` is a discriminated union. Every printed literal is represented:

| Family | Model | Parameters and literals |
| --- | --- | --- |
| ISO 8802-3 | `Iso8802_3` | `10BASE5`, `10BASE2`, `10BASET`, `fiber` |
| ARCNET | `Arcnet` | `coax star`, `coax bus`, `twisted pair star`, `twisted pair bus`, `fiber star`, `twisted pair, EIA-485`; rates required only for EIA-485 |
| MS/TP | `MsTp` | `manager`, `subordinate`; nonempty rates |
| Point-To-Point | `PointToPoint` | `EIA 232`, `Modem`; rates or modem autobaud range |
| BACnet/IP | `BacnetIp` | `'DIX' Ethernet`, `Other` |
| BACnet/IPv6 | `BacnetIpv6` | `'DIX' Ethernet` |
| BACnet/SC | `BacnetSc` | No parameters |
| Zigbee | `Zigbee` | No parameters |
| Other | `Other` | Optional lenient description |

Each class exposes `regex` and `canonical_text()`. The period in MS/TP and Point-To-Point and the comma in ARCNET are retained. Omitting 9600 from MS/TP produces a warning.

## Character sets (4.5.6)

```text
Character Sets Supported: { ISO 10646 (UTF-8) }
```

`CharacterSet` covers UTF-8, IBM/Microsoft DBCS, JIS X 0208, ISO 8859-1, UCS-4, and UCS2. UCS-2 and the trademarked DBCS spelling are aliases, as are case and redundant spaces. This list is independent of the file encoding.

## Special functionality (4.5.7)

```text
Special Functionality: { Maximum APDU size in octets: 1476 }
```

| Printed keyword | `SpecialFunctionality` field |
| --- | --- |
| Maximum APDU size in octets | `max_apdu_size` |
| Segmented Requests Supported, window size | `segmented_requests_window` |
| Segmented Responses Supported, window size | `segmented_responses_window` |
| Router | `router` |
| BACnet/IP BBMD | `bacnet_ip_bbmd` |
| BACnet/IPV6 BBMD | `bacnet_ipv6_bbmd` |
| BACnet/SC Hub | `bacnet_sc_hub` |
| BACnet/SC Direct Connect | `bacnet_sc_direct_connect` |

Numeric parameters require nonnegative integers. Windows outside 1..127 produce warnings. `unknown` preserves lenient unrecognized feature lines.

## Default restrictions (4.5.8)

```text
Default Property Value Restrictions:
{
    real: <minimum: 0.0; maximum: 100.0; resolution: 0.1>
}
```

`Restrictions` preserves minimum, maximum, and resolution as typed value nodes. It also has `maximum_length_string`, `maximum_length_list`, `maximum_length_array`, and `allowed_values` (named tokens). `merge(default, override)` applies defined override fields.

| Datatype alias | `DefaultRestrictions` field | Printed restrictions |
| --- | --- | --- |
| unsigned-integer | `unsigned_integer` | minimum, maximum |
| signed-integer | `signed_integer` | minimum, maximum |
| real | `real` | minimum, maximum, resolution |
| double | `double` | minimum, maximum, resolution |
| date | `date` | minimum, maximum |
| octet-string | `octet_string` | maximum length string |
| character-string | `character_string` | maximum length string |
| list | `list` | maximum length list |
| variable-length-array | `variable_length_array` | maximum length array |

Unlisted restrictions produce warnings. `extra` holds lenient datatype extensions, including Time defaults implied elsewhere in Clause 4.4.2.

## Fail times (4.5.9)

```text
Fail Times: { Notification Fail Time: 10.0 }
```

`FailTimes` has every printed timer: Notification, Internal Processing, Minimum ON/OFF, Schedule Evaluation, External Command, Program Object State Change, Acknowledgement, Subordinate Proxy Confirm Interval, Unconfirmed Response, Channel Write, Auto Negotiation, Activate Changes, and Foreign Device Registration. It also includes Audit Notification Forwarder (6.3.14). Each has a nonnegative finite seconds value; a missing value is represented by `None`. Parser mode determines completeness.

The template aliases are retained; `Acknowledgment Fail Time`, `Autonegotiation Fail Time`, and `Minimum ON/OFF Fail Time` map to the corresponding template fields. `extra` holds lenient additional timer names.

## Test database (4.5.10)

```text
List of Objects in Test Device:
{
    {
        object-identifier: (analog-value, 6)
        object-name: "AV6"
        object-type: analog-value
        present-value: 23.4 W
    }
}
```

`TestObject` has `identifier`, `name`, `object_type`, and ordered `properties`. The three headers are excluded from `properties`. Their optional access, restrictions, comments, and unreadable marker are stored in `header_metadata`, keyed by canonical header name. `PropertyMetadata` carries these four attributes; omitted entries use readable access and no other metadata. Header values remain derived from the three dedicated fields. `PropertyEntry` stores `name`, `value`, `access` (R/W/C), `restrictions`, `comment`, and `not_readable`. Duplicate identifiers, duplicate property names, repeated headers, mismatched types, and extra proprietary-object properties are rejected. A proprietary object has a numeric type of at least 128 and only its headers. Instance numbers range from 0 through 4194303.

`EpicsDocument.device`, `get_object()`, `objects_of_type()`, and the three `supports_*()` helpers expose declarations without external knowledge. Missing or multiple Device objects warn. Native `not_readable` syntax is the extension comment described in decision 0004.
