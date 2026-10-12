"""Regenerate six encoded synthetic fixtures without copied standard text."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from ace_epics.codecs.epics import dumps
from ace_epics.encoding import encode
from tests.fixtures_build_epics import BASE, minimal, write


def main():
    for code in range(6):
        doc = minimal()
        doc.header.charset_code = code
        write(BASE / "encodings" / f"minimal-{code}.tpi", encode(dumps(doc), code))


if __name__ == "__main__":
    main()
