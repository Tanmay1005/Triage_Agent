import json
import gradio as gr
from graph.pipeline import run_triage
from agents.dedup import init_vector_store, seed_vector_store
from agents.jira_client import create_jira_ticket

# Initialize ChromaDB on startup
collection = init_vector_store()
seed_vector_store(collection)

EXAMPLE_INPUTS = [
    "The login button on the checkout page is unresponsive on Safari. Works on Chrome.",
    "it's broken",
    "Stripe payments over $10,000 are timing out and customers aren't getting confirmation emails",
    "Would be nice if the dashboard had dark mode",
    "URGENT: User passwords exposed in plaintext in /api/v2/users response",
]

# Store the latest Jira payload for the "Create in Jira" button
_latest_jira_payload = {"payload": None}


def process_ticket(raw_input: str):
    """Run the full triage pipeline and return formatted outputs for each tab."""
    if not raw_input.strip():
        return "Please enter a bug report.", "", "", "", "", gr.update(visible=False), ""

    result = run_triage(raw_input)

    # Tab 1: Intake
    if result.get("parsed_ticket"):
        pt = result["parsed_ticket"]
        intake_output = json.dumps(pt.model_dump(), indent=2)
    elif result.get("error"):
        intake_output = json.dumps({"error": result["error"]}, indent=2)
    else:
        intake_output = json.dumps({"status": "no output"}, indent=2)

    # Tab 2: Dedup
    if result.get("dedup_result"):
        dedup_output = json.dumps(result["dedup_result"].model_dump(), indent=2)
    else:
        dedup_output = json.dumps(
            {"status": "Skipped (input was invalid or needs clarification)"}, indent=2
        )

    # Tab 3: Labels
    if result.get("labeled_ticket"):
        labeled_output = json.dumps(result["labeled_ticket"].model_dump(), indent=2)
    else:
        labeled_output = json.dumps({"status": "Skipped"}, indent=2)

    # Tab 4: Routing + Jira Payload
    if result.get("team_assignment") and result.get("jira_payload"):
        route_output = json.dumps(
            {
                "assignment": result["team_assignment"].model_dump(),
                "jira_payload": result["jira_payload"].model_dump(),
            },
            indent=2,
        )
        # Store payload for Jira creation
        _latest_jira_payload["payload"] = result["jira_payload"].model_dump()
    else:
        route_output = json.dumps({"status": "Skipped"}, indent=2)
        _latest_jira_payload["payload"] = None

    # Tab 5: Trace
    trace_output = f"Decision: {result.get('decision', 'unknown')}\n\n"
    trace_output += "Pipeline Trace:\n"
    for step in result.get("trace", []):
        trace_output += f"  -> {step}\n"

    # Show/hide Jira button based on decision
    show_jira_btn = result.get("decision") == "create_ticket"

    return (
        intake_output,
        dedup_output,
        labeled_output,
        route_output,
        trace_output,
        gr.update(visible=show_jira_btn),
        "",  # Clear any previous Jira result
    )


def create_in_jira():
    """Create the triaged ticket in Jira Cloud."""
    payload = _latest_jira_payload.get("payload")
    if not payload:
        return "No ticket payload available. Run triage first."

    result = create_jira_ticket(payload)

    if result.success:
        return f"Jira ticket **{result.key}** created\n\n{result.url}"
    else:
        return f"Failed to create Jira ticket: {result.error}"


# Build UI
with gr.Blocks(title="Sentinel — AI Triage Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # Sentinel — Autonomous Triage Agent
        Paste a raw bug report, support message, or incident description.
        Watch the multi-agent pipeline parse, deduplicate, classify, and route it.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            input_text = gr.Textbox(
                label="Raw Bug Report",
                placeholder="e.g., The login button on the checkout page is unresponsive on Safari...",
                lines=5,
            )
            submit_btn = gr.Button("Run Triage", variant="primary")
            gr.Examples(
                examples=[[ex] for ex in EXAMPLE_INPUTS],
                inputs=input_text,
                label="Try these examples",
            )

            gr.Markdown("---")
            create_jira_btn = gr.Button(
                "Create in Jira",
                variant="secondary",
                visible=False,
            )
            jira_result = gr.Markdown(label="Jira Result")

        with gr.Column(scale=2):
            with gr.Tab("1. Intake Parse"):
                intake_out = gr.Code(language="json", label="Parsed Ticket")
            with gr.Tab("2. Dedup Check"):
                dedup_out = gr.Code(language="json", label="Dedup Result")
            with gr.Tab("3. Labels & Severity"):
                label_out = gr.Code(language="json", label="Classification")
            with gr.Tab("4. Routing & Jira Payload"):
                route_out = gr.Code(language="json", label="Assignment + Jira Payload")
            with gr.Tab("5. Pipeline Trace"):
                trace_out = gr.Textbox(label="Execution Trace", lines=10)

    submit_btn.click(
        fn=process_ticket,
        inputs=input_text,
        outputs=[
            intake_out,
            dedup_out,
            label_out,
            route_out,
            trace_out,
            create_jira_btn,
            jira_result,
        ],
    )

    create_jira_btn.click(
        fn=create_in_jira,
        inputs=[],
        outputs=jira_result,
    )

if __name__ == "__main__":
    demo.launch()
