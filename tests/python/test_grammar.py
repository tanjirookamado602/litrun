"""
Unit Tests for litrun Structured Output Engine & GBNF Grammar Generation
"""

import json
from litrun.grammar import (
    STANDARD_JSON_GBNF,
    json_schema_to_gbnf,
    resolve_grammar,
)
from litrun.model import Model


def test_standard_json_gbnf():
    assert "root ::=" in STANDARD_JSON_GBNF
    assert "object" in STANDARD_JSON_GBNF
    assert "array" in STANDARD_JSON_GBNF
    assert "string" in STANDARD_JSON_GBNF
    assert "number" in STANDARD_JSON_GBNF


def test_json_schema_to_gbnf_simple():
    schema = {
        "type": "object",
        "properties": {
            "sensor": {"type": "string"},
            "temperature": {"type": "number"},
            "active": {"type": "boolean"},
            "status": {"enum": ["nominal", "warning", "critical"]},
        },
        "required": ["sensor", "temperature", "status"],
    }
    gbnf = json_schema_to_gbnf(schema)
    assert "root ::=" in gbnf
    assert '"sensor"' in gbnf
    assert '"temperature"' in gbnf
    assert '"nominal"' in gbnf
    assert '"critical"' in gbnf
    assert "ws ::=" in gbnf


def test_resolve_grammar_variations():
    # 1. String shortcut
    g1 = resolve_grammar("json")
    assert g1 == STANDARD_JSON_GBNF

    g2 = resolve_grammar("json_object")
    assert g2 == STANDARD_JSON_GBNF

    # 2. OpenAI dict format
    g3 = resolve_grammar({"type": "json_object"})
    assert g3 == STANDARD_JSON_GBNF

    # 3. OpenAI json_schema format
    schema_dict = {
        "type": "object",
        "properties": {
            "alert": {"type": "boolean"},
        },
    }
    g4 = resolve_grammar({
        "type": "json_schema",
        "json_schema": {"schema": schema_dict},
    })
    assert g4 is not None
    assert "root ::=" in g4
    assert '"alert"' in g4

    # 4. None for empty
    assert resolve_grammar(None) is None


def test_mock_model_structured_output():
    with Model.load("qwen2.5-0.5b", allow_mock=True) as model:
        res = model.generate(
            "Telemetry check",
            response_format={"type": "json_object"},
        )
        parsed = json.loads(res)
        assert parsed.get("status") == "ok"
        assert "telemetry" in parsed


if __name__ == "__main__":
    test_standard_json_gbnf()
    test_json_schema_to_gbnf_simple()
    test_resolve_grammar_variations()
    test_mock_model_structured_output()
    print("All grammar tests passed!")
