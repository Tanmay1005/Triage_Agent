import pytest
from graph.pipeline import run_triage
from agents.dedup import init_vector_store, seed_vector_store

pytestmark = pytest.mark.llm


@pytest.fixture(scope="module", autouse=True)
def ensure_seeded():
    """Ensure ChromaDB is seeded before pipeline tests."""
    collection = init_vector_store()
    seed_vector_store(collection)


class TestFullPipeline:
    def test_clear_bug_creates_ticket(self):
        result = run_triage(
            "The payment confirmation email is not being sent after successful "
            "Stripe transactions over $500. Affects all users."
        )
        assert result["decision"] == "create_ticket"
        assert result["parsed_ticket"] is not None
        assert result["parsed_ticket"].is_valid is True
        assert result["labeled_ticket"] is not None
        assert result["team_assignment"] is not None
        assert result["jira_payload"] is not None

    def test_vague_input_stops_at_clarification(self):
        result = run_triage("doesn't work")
        assert result["decision"] == "needs_clarification"
        assert result["labeled_ticket"] is None
        assert result["team_assignment"] is None

    def test_security_incident_gets_critical_severity(self):
        result = run_triage(
            "URGENT: SQL injection vulnerability found in the search endpoint. "
            "Attacker can extract user data via the q parameter."
        )
        assert result["decision"] == "create_ticket"
        assert result["labeled_ticket"].severity.value in ["critical", "high"]

    def test_feature_request_gets_low_severity(self):
        result = run_triage(
            "Would be nice to have a dark mode option in the dashboard settings"
        )
        assert result["decision"] == "create_ticket"
        assert result["labeled_ticket"].severity.value in ["low", "medium"]
        assert result["labeled_ticket"].issue_type.value == "feature_request"

    def test_all_trace_steps_present_for_full_pipeline(self):
        result = run_triage(
            "The analytics CSV export is missing column headers since the last deploy"
        )
        if result["decision"] == "create_ticket":
            trace_text = " ".join(result["trace"])
            assert "INTAKE" in trace_text
            assert "DEDUP" in trace_text
            assert "LABELER" in trace_text
            assert "ROUTER" in trace_text

    def test_empty_input(self):
        result = run_triage("")
        assert result["decision"] == "needs_clarification" or result.get("error") is not None

    def test_jira_payload_has_required_fields(self):
        result = run_triage(
            "The checkout page shows $0.00 for subscription plans instead of actual price"
        )
        if result["decision"] == "create_ticket":
            fields = result["jira_payload"].fields
            assert "project" in fields
            assert "summary" in fields
            assert "description" in fields
            assert "issuetype" in fields
