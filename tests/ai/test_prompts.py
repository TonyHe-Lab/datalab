import pytest
from src.ai.prompt_templates import (
    build_extraction_prompt,
    validate_ai_json,
    FEW_SHOT_EXAMPLES,
)


def test_build_extraction_prompt_includes_examples():
    text = "Test maintenance log."
    prompt = build_extraction_prompt(text)
    assert "Example Input:" in prompt
    assert "Example Output:" in prompt
    assert text in prompt
    assert "Output:" in prompt
    # Check that all examples are included
    for example in FEW_SHOT_EXAMPLES:
        assert example["input"] in prompt


def test_validate_ai_json_valid():
    valid_data = {
        "main_component_ai": "Pump",
        "primary_symptom_ai": "noise",
        "root_cause_ai": "wear",
        "summary_ai": "Pump noisy",
        "solution_ai": "replace",
    }
    assert validate_ai_json(valid_data) is True


def test_validate_ai_json_invalid_missing_key():
    invalid_data = {
        "main_component_ai": "Pump",
        "primary_symptom_ai": "noise",
        "root_cause_ai": "wear",
        "summary_ai": "Pump noisy",
        # missing solution_ai
    }
    assert validate_ai_json(invalid_data) is False


def test_validate_ai_json_invalid_extra_key():
    invalid_data = {
        "main_component_ai": "Pump",
        "primary_symptom_ai": "noise",
        "root_cause_ai": "wear",
        "summary_ai": "Pump noisy",
        "solution_ai": "replace",
        "extra": "field",
    }
    assert validate_ai_json(invalid_data) is False
