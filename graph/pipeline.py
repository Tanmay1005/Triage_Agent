from langgraph.graph import StateGraph, END
from schema.state import TriageState
from agents.intake import intake_agent
from agents.dedup import dedup_agent
from agents.labeler import labeler_agent
from agents.router import router_agent


def should_continue_after_intake(state: TriageState) -> str:
    """Route based on intake result."""
    if state.get("error"):
        return "error"
    if state.get("decision") == "needs_clarification":
        return "clarification"
    return "dedup"


def should_continue_after_dedup(state: TriageState) -> str:
    """Route based on dedup result."""
    if state.get("dedup_result") and state["dedup_result"].is_duplicate:
        return "duplicate"
    return "label"


def build_pipeline() -> StateGraph:
    """Construct the LangGraph triage pipeline."""
    workflow = StateGraph(TriageState)

    # Add nodes
    workflow.add_node("intake", intake_agent)
    workflow.add_node("dedup", dedup_agent)
    workflow.add_node("labeler", labeler_agent)
    workflow.add_node("router", router_agent)

    # Set entry point
    workflow.set_entry_point("intake")

    # Conditional edges
    workflow.add_conditional_edges(
        "intake",
        should_continue_after_intake,
        {
            "dedup": "dedup",
            "clarification": END,
            "error": END,
        },
    )

    workflow.add_conditional_edges(
        "dedup",
        should_continue_after_dedup,
        {
            "label": "labeler",
            "duplicate": END,
        },
    )

    # Linear edges
    workflow.add_edge("labeler", "router")
    workflow.add_edge("router", END)

    return workflow.compile()


# Global compiled pipeline instance
pipeline = build_pipeline()


def run_triage(raw_input: str, input_type: str = "text") -> TriageState:
    """Execute the full triage pipeline."""
    initial_state: TriageState = {
        "raw_input": raw_input,
        "input_type": input_type,
        "normalized_text": None,
        "parsed_ticket": None,
        "dedup_result": None,
        "labeled_ticket": None,
        "team_assignment": None,
        "jira_payload": None,
        "decision": None,
        "error": None,
        "trace": [],
    }

    result = pipeline.invoke(initial_state)
    return result
