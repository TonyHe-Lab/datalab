"""Integration tests for text analyzer with mocked Azure OpenAI API."""

import json
import pytest
from unittest.mock import Mock, patch
from src.ai.text_analyzer import analyze_text
from src.ai.openai_client import AzureOpenAIClient


@pytest.fixture
def mock_client():
    client = Mock(spec=AzureOpenAIClient)
    client.chat_completion.return_value = {
        "content": json.dumps(
            {
                "main_component_ai": "Pump System",
                "primary_symptom_ai": "Leakage detected",
                "root_cause_ai": "Seal failure",
                "summary_ai": "Pump seal needs replacement",
                "solution_ai": "Replace pump seal and test system",
            }
        )
    }
    return client


def test_analyze_text_success(mock_client):
    """Test successful text analysis with mocked API."""
    notification_id = "test-123"
    text = "The pump is leaking water. Patient ID: 12345"

    result = analyze_text(notification_id, text, mock_client)

    assert result["success"] is True
    assert "data" in result
    data = result["data"]
    assert data["notification_id"] == notification_id
    assert data["main_component_ai"] == "Pump System"
    assert data["primary_symptom_ai"] == "Leakage detected"
    assert data["root_cause_ai"] == "Seal failure"
    assert data["summary_ai"] == "Pump seal needs replacement"
    assert data["solution_ai"] == "Replace pump seal and test system"


def test_analyze_text_api_failure_fallback(mock_client):
    """Test fallback when API fails."""
    mock_client.chat_completion.side_effect = Exception("API unavailable")

    notification_id = "test-456"
    text = "Error in motor control system. Fault code: ERR-001"

    result = analyze_text(notification_id, text, mock_client)

    assert result["success"] is True
    assert "data" in result
    data = result["data"]
    assert data["notification_id"] == notification_id
    assert data["primary_symptom_ai"] is not None  # Should extract from text
    assert "Refer to standard operating procedures" in data["solution_ai"]


def test_analyze_text_invalid_json(mock_client):
    """Test handling of invalid JSON from API."""
    mock_client.chat_completion.return_value = {"content": "Invalid JSON response"}

    notification_id = "test-789"
    text = "System alert"

    result = analyze_text(notification_id, text, mock_client)

    assert result["success"] is False
    assert "error" in result
    assert "Invalid JSON" in result["error"]


def test_analyze_text_schema_validation_failure(mock_client):
    """Test handling of JSON that fails schema validation."""
    mock_client.chat_completion.return_value = {
        "content": json.dumps({"invalid_key": "value"})
    }

    notification_id = "test-999"
    text = "Test text"

    result = analyze_text(notification_id, text, mock_client)

    assert result["success"] is False
    assert "error" in result
    assert "schema validation" in result["error"]
