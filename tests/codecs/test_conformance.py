"""All registered codecs obey the same semantic model identity contract."""

from io import BytesIO, StringIO
from pathlib import Path

import pytest

from ace_epics import convert, dump, load
from ace_epics.codecs import registry
from ace_epics.codecs.epics import loads

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def full():
    return loads((ROOT / "tests/fixtures/epics/full.tpi").read_bytes(), strict=True)


@pytest.mark.parametrize("codec", registry.codecs(), ids=lambda c: c.name)
def test_semantic_identity_text_bytes_files_streams(codec, full, tmp_path):
    encoded = codec.dumps(full)
    assert codec.loads(encoded) == full
    assert codec.loads(encoded.encode() if isinstance(encoded, str) else encoded) == full
    path = tmp_path / ("document" + codec.extensions[0])
    codec.dump(full, path)
    assert codec.load(path) == full
    if codec.name == "epics":
        binary = BytesIO()
        codec.dump(full, binary)
        assert codec.load(BytesIO(binary.getvalue())) == full
    else:
        text = StringIO()
        codec.dump(full, text)
        assert codec.load(StringIO(text.getvalue())) == full
    assert codec.load(BytesIO(path.read_bytes())) == full


@pytest.mark.parametrize("codec", registry.codecs(), ids=lambda c: c.name)
def test_writer_determinism(codec, full):
    opts = {"deterministic": True} if codec.name == "rdf" else {}
    assert codec.dumps(full, **opts) == codec.dumps(full, **opts)


def test_cross_codec_cycle_and_top_level_file_api(full, tmp_path):
    source = tmp_path / "source.tpi"
    dump(full, source)
    for extension in (".json", ".yaml", ".ttl", ".tpi"):
        target = tmp_path / ("converted" + extension)
        convert(source, target)
        source = target
    assert load(source) == full
    assert loads(source.read_bytes(), strict=True).diagnostics == []


def test_registry_aliases_unknown_names_and_extension_collision():
    assert registry.get("native") is registry.get("epics")
    assert registry.get("turtle") is registry.get("rdf")
    assert registry.for_path("EXAMPLE.TPI").name == "epics"
    with pytest.raises(ValueError, match="Unknown codec"):
        registry.get("unknown")
    with pytest.raises(ValueError, match="Cannot infer"):
        registry.for_path("unknown.blob")
    with pytest.raises(ValueError, match="already registered"):
        registry.register(registry.get("json"))
    duplicate = registry.ModuleCodec("duplicate", (".JSON",), "application/json", "json")
    with pytest.raises(ValueError, match="extension"):
        registry.register(duplicate)
