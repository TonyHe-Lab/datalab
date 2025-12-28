"""Prompt templates used for structured extraction and few-shot examples.

Store prompt strings and small helpers for building messages used by
the Azure OpenAI client.
"""

EXTRACTION_PROMPT = """
You are an expert maintenance log analyst.
Extract the following fields using the project's canonical field names as strict JSON:
{
    "main_component_ai": "string",
    "primary_symptom_ai": "string",
    "root_cause_ai": "string",
    "summary_ai": "string",
    "solution_ai": "string"
}

Rules:
- Return ONLY a single JSON object and nothing else.
- Do not include comments or trailing commas.
- If a field is unknown, use an empty string or empty array.
- Keep the summary concise (<= 30 words).
- Use the exact key names shown above (with `_ai` suffixes) to match system schemas.
 - If the input is not English, first translate into English internally, then extract and return JSON in English.
 - Do not include any personal identifiers; never echo back names, emails, phone numbers, MRNs, or dates.
"""

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "main_component_ai": {"type": "string"},
        "primary_symptom_ai": {"type": "string"},
        "root_cause_ai": {"type": "string"},
        "summary_ai": {"type": "string"},
        "solution_ai": {"type": "string"},
    },
    "required": [
        "main_component_ai",
        "primary_symptom_ai",
        "root_cause_ai",
        "summary_ai",
        "solution_ai",
    ],
    "additionalProperties": False,
}

FEW_SHOT_EXAMPLES = [
    {
        "input": "Pump A failed due to overheating; bearing was worn and replaced.",
        "output": {
            "main_component_ai": "Pump A",
            "primary_symptom_ai": "overheating",
            "root_cause_ai": "worn bearing",
            "summary_ai": "Pump A overheated; bearing replaced",
            "solution_ai": "replace bearing; test pump",
        },
    },
    {
        "input": "Ventilator filter clogged, causing reduced airflow; cleaned and replaced filter.",
        "output": {
            "main_component_ai": "Ventilator",
            "primary_symptom_ai": "reduced airflow",
            "root_cause_ai": "clogged filter",
            "summary_ai": "Ventilator filter clogged; cleaned and replaced",
            "solution_ai": "clean or replace filter",
        },
    },
    {
        "input": "Patient reported fever; thermostat malfunctioned, set to high temperature.",
        "output": {
            "main_component_ai": "Thermostat",
            "primary_symptom_ai": "fever reported",
            "root_cause_ai": "malfunctioned thermostat",
            "summary_ai": "Thermostat malfunction caused fever; adjusted settings",
            "solution_ai": "adjust thermostat; monitor temperature",
        },
    },
    {
        "input": "Bearing in pump B making noise; lubrication low, refilled and inspected.",
        "output": {
            "main_component_ai": "Pump B",
            "primary_symptom_ai": "noise",
            "root_cause_ai": "low lubrication",
            "summary_ai": "Pump B bearing noisy; lubrication refilled",
            "solution_ai": "refill lubrication; inspect bearing",
        },
    },
]


def build_extraction_prompt(text: str) -> str:
    """Build the full extraction prompt including few-shot examples."""
    import json

    prompt = EXTRACTION_PROMPT.strip()
    for example in FEW_SHOT_EXAMPLES:
        prompt += f"\n\nExample Input: {example['input']}\nExample Output: {json.dumps(example['output'])}"
    prompt += f"\n\nInput: {text}\nOutput:"
    return prompt


def validate_ai_json(data: dict) -> bool:
    """Validate AI JSON against the strict schema.

    Returns True if valid, otherwise False. Avoids importing Pydantic here to keep
    prompt module lightweight; uses jsonschema if available, otherwise manual checks.
    """
    try:
        from jsonschema import validate
        from jsonschema.exceptions import ValidationError

        validate(instance=data, schema=JSON_SCHEMA)
        return True
    except ImportError:
        # Fallback: minimal manual validation
        keys = [
            "main_component_ai",
            "primary_symptom_ai",
            "root_cause_ai",
            "summary_ai",
            "solution_ai",
        ]
        if not all(k in data for k in keys):
            return False
        if len(data) != len(keys):
            return False  # no extra keys
        if not isinstance(data.get("solution_ai"), str):
            return False
        return True
    except Exception:
        return False
