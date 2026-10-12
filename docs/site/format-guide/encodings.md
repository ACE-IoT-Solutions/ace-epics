# Encodings

An EPICS byte stream begins with `PICS n` and a CRLF terminator. The character-set
number controls decoding; it is independent of BACnet protocol revision.

| Code | Charset | Python codec | Bytes per header character |
| --- | --- | --- | --- |
| 0 | UTF-8 | `utf-8` | 1 |
| 1 | Microsoft DBCS | `mbcs` on Windows, `cp932` elsewhere | 1 |
| 2 | JIS X 0208 | `iso2022_jp` | 1 |
| 3 | UCS-4 | `utf-32-be` | 4 |
| 4 | UCS-2 | `utf-16-be` | 2 |
| 5 | ISO 8859-1 | `latin-1` | 1 |

The DBCS number does not identify a particular code page. On non-Windows systems,
CP932 is an explicit interoperability choice and produces `E-DBCS`. JIS is encoded
as ISO-2022-JP rather than Shift JIS, so its ASCII header remains recognizable.
The UCS-2 implementation uses Python's UTF-16 codec, including surrogate support.

```python
from ace_epics.encoding import decode, encode

text, detected, diagnostics = decode(b"PICS 0\r\n")
assert detected.charset_code == 0
assert encode(text, 0) == b"PICS 0\r\n"
```

`detect()` recognizes the one-, two-, and four-byte header patterns without decoding
an entire file. `decode()` preserves line endings and returns diagnostic evidence.
An unknown charset produces `E-CHARSET` and continues with UTF-8. Missing or malformed
header digits produce `E-HEADER`; a mismatch between the header digit and character
width produces `E-WIDTH`. Invalid encoded data is replaced with the Unicode replacement
character and reported as `E-DECODE`.

Byte-order marks (`E-BOM`), little-endian wide streams (`E-ENDIAN`), noncanonical
header case or spacing (`E-HEADER-FORM`), and bare LF or CR line endings
(`E-LINE-ENDINGS`) are warnings by default and errors with `strict=True`.
The writer's `encode()` always emits BOM-free big-endian wide streams.
