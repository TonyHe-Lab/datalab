"""Prompt templates used for structured extraction and few-shot examples.

Store prompt strings and small helpers for building messages used by
the Azure OpenAI client.
"""

EXTRACTION_PROMPT = """
Extract the following fields as JSON: component, fault, cause, summary, resolution_steps.
Ensure output is valid JSON strictly matching the provided schema.
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": "Pump A failed due to overheating, replaced bearing.",
        "output": {
            "component": "Pump A",
            "fault": "overheating",
            "cause": "worn bearing",
            "summary": "Pump A overheated; bearing replaced",
            "resolution_steps": ["replace bearing", "test pump"],
        },
    }
]
