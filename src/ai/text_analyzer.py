"""Orchestrator for text analysis: scrubbing, extraction and embeddings.

Initial orchestration wiring to be expanded in subsequent iterations.
"""

"""Text analysis orchestration module.

Coordinates PII scrubbing, prompt generation, and Azure OpenAI client calls.
Performs JSON validation against project schemas.
"""

from typing import Dict, Any, List
import json
from .pii_scrubber import redact_pii, contains_medical_terms
from .openai_client import AzureOpenAIClient

from src.ai.prompt_templates import (
    EXTRACTION_PROMPT,
    FEW_SHOT_EXAMPLES,
    validate_ai_json,
)
from src.models.schemas import AIExtractedDataCreate


def build_messages(redacted_text: str) -> list:
    """Build chat messages with system prompt and few-shot example, plus user text."""
    messages = [
        {"role": "system", "content": EXTRACTION_PROMPT.strip()},
    ]
    # Include one few-shot to guide format
    if FEW_SHOT_EXAMPLES:
        ex = FEW_SHOT_EXAMPLES[0]
        messages.append(
            {
                "role": "user",
                "content": ex["input"],
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(ex["output"], ensure_ascii=False),
            }
        )
    # Finally the real user text
    messages.append({"role": "user", "content": redacted_text})
    return messages


def analyze_text(
    notification_id: str, text: str, client: AzureOpenAIClient
) -> Dict[str, Any]:
    """End-to-end analysis: scrub PII, query Azure, validate JSON, and cast to schema.

    Returns dict with keys: success, data (schema instance dict), error.
    """
    # PII scrub
    redacted_text, _details = redact_pii(text)

    # Build messages
    messages = build_messages(redacted_text)

    # Call Azure
    # Hint: adjust max_tokens when medical terms are present (slightly larger)
    kwargs = {}
    if contains_medical_terms(redacted_text):
        kwargs["max_tokens"] = 1200
    try:
        result = client.chat_completion(messages, **kwargs)
        content = result.get("content", "")
    except Exception:
        # Fallback to rule-based extraction (AC-6)
        # Very simple heuristic: extract keywords as unique words, primary symptom via pattern
        tokens: List[str] = [w.strip(",.;:()[]{}") for w in redacted_text.split()]
        keywords = sorted(list({t.lower() for t in tokens if len(t) > 4}))[:10]
        fallback = {
            "main_component_ai": None,
            "primary_symptom_ai": next(
                (t for t in tokens if "error" in t.lower() or "fault" in t.lower()),
                None,
            ),
            "root_cause_ai": None,
            "summary_ai": redacted_text[:200],
            "solution_ai": "Refer to standard operating procedures; manual triage initiated.",
            "keywords_ai": keywords,
        }
        try:
            ai_data = AIExtractedDataCreate(
                notification_id=notification_id,
                **fallback,
            )
            return {"success": True, "data": ai_data.model_dump()}
        except Exception as e:
            return {"success": False, "error": f"Fallback validation error: {e}"}

    # Try parse JSON
    try:
        parsed = json.loads(content)
    except Exception:
        return {"success": False, "error": "Invalid JSON returned by model"}

    # Validate against schema
    if not validate_ai_json(parsed):
        return {"success": False, "error": "JSON failed schema validation"}

    # Cast to Pydantic schema (AIExtractedDataCreate)
    try:
        ai_data = AIExtractedDataCreate(
            notification_id=notification_id,
            main_component_ai=parsed.get("main_component_ai"),
            primary_symptom_ai=parsed.get("primary_symptom_ai"),
            root_cause_ai=parsed.get("root_cause_ai"),
            summary_ai=parsed.get("summary_ai"),
            solution_ai=parsed.get("solution_ai"),
        )
        return {"success": True, "data": ai_data.model_dump()}
    except Exception as e:
        return {"success": False, "error": f"Pydantic validation error: {e}"}


class TextAnalyzer:
    def __init__(self, client: AzureOpenAIClient):
        self.client = client

    def analyze(self, text: str) -> Dict[str, Any]:
        # Step 1: redact PII
        redacted, details = redact_pii(text)

        # Step 2: placeholder for structured extraction (call to client.chat_completion)
        # For now, we return redacted text and detected details to allow unit testing.
        return {
            "redacted_text": redacted,
            "pii_details": details,
        }
