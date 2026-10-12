# ADR 0002: Two-layer value model

Date: 2026-10-11
Status: accepted

## Context

EPICS values are text whose BACnet datatypes are determined by property definitions
outside ASHRAE 135.1. Parentheses can represent dates, object identifiers, and lists.
Parsing should work even when no external knowledge provider is installed.

## Decision

Parse a syntactic ValueNode tree without consulting BACnet knowledge. Represent
scalars, groups, context tags, and unspecified values explicitly. An optional
interpretation layer resolves ambiguous nodes against a declared BACnet datatype.
The Pydantic document model is shared by native, JSON, YAML, and RDF codecs.

## Consequences

Unknown datatypes never prevent syntactic parsing. Interpretation can supply more
specific meaning without replacing the original syntax. Semantic round trips are
required; byte-for-byte preservation of layout is not. Validation reports missing
knowledge as skipped checks instead of silently accepting unknown requirements.
