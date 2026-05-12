"""Smoke tests (no API key)."""

from core import parse_model_json
from schemas.extraction import ExtractionResponse


def test_parse_fenced_json():
    raw = """```json
{"fields": [{"field_name": "Borrower Name", "field_value": "Jane", "confidence_score": 0.9}]}
```"""
    d = parse_model_json(raw)
    assert d["fields"][0]["field_name"] == "Borrower Name"


def test_schema_roundtrip():
    d = parse_model_json(
        '{"fields": [{"field_name": "X", "field_value": "1", "confidence_score": 1}]}'
    )
    m = ExtractionResponse.model_validate({"fields": d["fields"], "grounding_sources": ["chunk-a"]})
    assert m.fields[0].field_value == "1"
    assert m.grounding_sources == ["chunk-a"]


if __name__ == "__main__":
    test_parse_fenced_json()
    test_schema_roundtrip()
    print("ok")
