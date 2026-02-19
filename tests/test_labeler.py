import pytest
from agents.labeler import labeler_agent
from schema.ticket import ParsedTicket
from schema.enums import Severity, Priority, IssueType

# Mark all tests in this file as requiring LLM
pytestmark = pytest.mark.llm


class TestLabelerAgent:
    def _make_state(self, title, description, component=None):
        return {
            "raw_input": description,
            "input_type": "text",
            "normalized_text": None,
            "parsed_ticket": ParsedTicket(
                title=title,
                description=description,
                component=component,
                is_valid=True,
            ),
            "dedup_result": None,
            "labeled_ticket": None,
            "team_assignment": None,
            "jira_payload": None,
            "decision": None,
            "error": None,
            "trace": [],
        }

    def test_security_incident_gets_critical(self):
        state = self._make_state(
            "SQL injection in search endpoint",
            "The /api/v2/search endpoint does not sanitize the q parameter. "
            "Union-based SQL injection confirmed. Can extract user data.",
            "security",
        )
        result = labeler_agent(state)
        assert result["labeled_ticket"] is not None
        assert result["labeled_ticket"].severity in [Severity.CRITICAL, Severity.HIGH]

    def test_feature_request_gets_low_severity(self):
        state = self._make_state(
            "Add dark mode to dashboard",
            "Users have requested a dark mode option in the dashboard settings.",
            "dashboard",
        )
        result = labeler_agent(state)
        lt = result["labeled_ticket"]
        assert lt is not None
        assert lt.severity in [Severity.LOW, Severity.MEDIUM]
        assert lt.issue_type == IssueType.FEATURE_REQUEST

    def test_bug_report_classified_as_bug(self):
        state = self._make_state(
            "Login button broken on Safari",
            "The login button on the checkout page doesn't respond to clicks on Safari 17.",
            "checkout",
        )
        result = labeler_agent(state)
        assert result["labeled_ticket"].issue_type == IssueType.BUG

    def test_labels_are_relevant(self):
        state = self._make_state(
            "Payment timeout for large transactions",
            "Stripe payments over $10,000 time out. Charge succeeds but no confirmation.",
            "payments",
        )
        result = labeler_agent(state)
        labels = result["labeled_ticket"].labels
        assert len(labels) > 0
        # At least one payment-related label
        payment_labels = {"payment", "payments", "stripe", "billing", "checkout", "transaction"}
        assert any(l.lower() in payment_labels for l in labels)

    def test_confidence_is_valid(self):
        state = self._make_state(
            "CSS broken on mobile",
            "Product cards overlap on screens smaller than 375px.",
            "ui",
        )
        result = labeler_agent(state)
        assert 0.0 <= result["labeled_ticket"].confidence <= 1.0

    def test_trace_is_populated(self):
        state = self._make_state(
            "Test issue",
            "Something is wrong with the system.",
        )
        result = labeler_agent(state)
        assert len(result["trace"]) > 0
        assert "LABELER" in result["trace"][0]
