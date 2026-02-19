import os
from agents._client import client, MODEL
from schema.ticket import LabeledTicket
from schema.state import TriageState

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "labeler_system.md")

def _load_prompt() -> str:
    with open(_PROMPT_PATH) as f:
        return f.read()

LABELER_PROMPT = _load_prompt()


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def labeler_agent(state: TriageState) -> dict:
    """Classify a parsed ticket with severity, priority, type, labels."""
    parsed = state["parsed_ticket"]

    ticket_text = f"Title: {parsed.title}\nDescription: {parsed.description}"
    if parsed.component:
        ticket_text += f"\nComponent: {parsed.component}"
    if parsed.steps_to_reproduce:
        ticket_text += f"\nSteps to reproduce: {parsed.steps_to_reproduce}"
    if parsed.environment:
        ticket_text += f"\nEnvironment: {parsed.environment}"

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=f"{LABELER_PROMPT}\n\n{ticket_text}",
        )

        content = _strip_code_fences(response.text)
        labeled = LabeledTicket.model_validate_json(content)

        return {
            "labeled_ticket": labeled,
            "trace": state.get("trace", []) + [
                f"LABELER: {labeled.severity.value}/{labeled.priority.value} "
                f"({labeled.issue_type.value}) confidence={labeled.confidence:.2f}"
            ],
        }

    except Exception as e:
        return {
            "error": f"Labeler failed: {str(e)}",
            "trace": state.get("trace", []) + [f"LABELER ERROR: {str(e)}"],
        }
