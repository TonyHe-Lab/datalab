import json
from src.ai.text_analyzer import analyze_text


class FailingClient:
    def chat_completion(self, *args, **kwargs):
        raise RuntimeError("Circuit open")


def test_analyze_text_fallback_rule_based():
    client = FailingClient()
    text = "Patient reported error code E123 on device. Troubleshooting started."
    res = analyze_text("N-FAKE", text, client)  # type: ignore
    assert res["success"] is True
    data = res["data"]
    assert data["notification_id"] == "N-FAKE"
    assert isinstance(data["summary_ai"], str)
    # primary_symptom_ai should pick up a token with 'error'
    assert data["primary_symptom_ai"] is not None
