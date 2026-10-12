# Native reader diagnostics

Diagnostics contain a code, severity, message, clause, and available source location. `P-*` codes describe whole-file or section parsing, `E-*` byte/line encoding, `V-*` value syntax, `R-*` restriction syntax, and `M-*` model advisories. `C5-*` and `S-*` are consistency checks documented in the validation rule registry.

Hard native-reader errors are listed below. Accepted deviations and their strictness behavior appear in [the leniency guide](../format-guide/leniency.md).

| Code | Meaning |
| --- | --- |
| `P-HEADER` | Missing/invalid `PICS` selector |
| `P-SIGNATURE`, `P-END` | Missing conformance signature or end line |
| `P-END-POSITION` | Content follows the terminating line |
| `P-SECTION-BRACE` | Missing/unclosed braced section |
| `P-DUPLICATE-SECTION` | A section occurs twice |
| `P-DATABASE-LAST` | A section follows the test database |
| `P-SERVICE-FLAGS` | Service has no direction or unsupported flags |
| `P-OBJECT-TYPE` | Invalid object-type declaration flags |
| `P-SPECIAL-INTEGER`, `P-SPECIAL-FLAG` | Incorrect special-feature parameter |
| `P-DEFAULT-RESTRICTION`, `P-ALLOWED-VALUES` | Malformed restriction or non-enumerated allowed value |
| `P-TIMER-VALUE` | Timer is not nonnegative finite real seconds |
| `P-DATABASE-ENTRY`, `P-OBJECT-BRACE` | Invalid content/object block in the database |
| `P-PROPERTY`, `P-PROPERTY-VALUE` | Missing property syntax/value |
| `P-VALUE-UNBALANCED`, `P-VALUE-CLOSER` | Value group recovery required |
| `P-OBJECT-HEADERS`, `P-OBJECT-IDENTIFIER` | Incorrect leading headers or missing instance |
| `P-OBJECT-MODEL`, `P-DOCUMENT-MODEL` | A recovered declaration violates model invariants |
| `P-RECOVERY` | Input exceeds recoverable syntax/type limits |

Model advisories include `M-DEVICE-COUNT`, `M-DUPLICATE-DECLARATION`, `M-BIBB-NAME`, `M-MSTP-9600`, `M-WINDOW-RANGE`, and `M-DEFAULT-RESTRICTION`. They remain warnings because their requirements depend on external BACnet knowledge or conventions rather than native grammar.
