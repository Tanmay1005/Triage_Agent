import os
from agents._client import client, MODEL
from schema.ticket import ParsedTicket
from schema.state import TriageState

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "intake_system.md")

def _load_prompt() -> str:
    with open(_PROMPT_PATH) as f:
        return f.read()

SYSTEM_PROMPT = _load_prompt()


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def intake_agent(state: TriageState) -> dict:
    """Parse raw input into structured ticket fields."""
    raw = state.get("normalized_text") or state["raw_input"]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Parse this bug report:\n\n{raw}"}
            ],
        )

        content = _strip_code_fences(response.content[0].text)
        parsed = ParsedTicket.model_validate_json(content)

        decision = "needs_clarification" if not parsed.is_valid else None
        trace_msg = (
            f"INTAKE: Parsed as '{parsed.title}'"
            if parsed.is_valid
            else f"INTAKE: Needs clarification — {parsed.clarification_reason}"
        )

        return {
            "parsed_ticket": parsed,
            "decision": decision,
            "trace": state.get("trace", []) + [trace_msg],
        }

    except Exception as e:
        return {
            "error": f"Intake agent failed: {str(e)}",
            "decision": "needs_clarification",
            "trace": state.get("trace", []) + [f"INTAKE ERROR: {str(e)}"],
        }
