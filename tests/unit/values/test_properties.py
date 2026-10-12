from hypothesis import given, settings
from hypothesis import strategies as st

from ace_epics.lexer import tokenize
from ace_epics.values import parse_value, render

from .values_strategies import value_nodes


def meaning(value):
    """Exclude lexical metadata while retaining all syntax and semantic fields."""
    data = value.model_dump()

    def clean(node):
        if isinstance(node, dict):
            if "canonical" in node:
                return {"canonical": node["canonical"]}
            return {
                key: clean(val)
                for key, val in node.items()
                if key
                not in {"text", "short", "quote", "trailing_comma", "parenthesised", "precision"}
            }
        if isinstance(node, list):
            return [clean(n) for n in node]
        return node

    return clean(data)


@given(value_nodes())
@settings(max_examples=2000, deadline=None)
def test_render_parse_roundtrip(node):
    rendered = render(node)
    parsed, _ = parse_value(rendered)
    assert meaning(parsed) == meaning(node)


@given(st.text(max_size=100))
@settings(max_examples=10000, deadline=None)
def test_arbitrary_input_never_raises(text):
    tokens, _ = tokenize(text)
    parse_value(tokens)
