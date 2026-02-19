import pytest
from agents.intake import intake_agent

# Mark all tests in this file as requiring LLM (slow, costs money)
pytestmark = pytest.mark.llm


class TestIntakeAgent:
    def _make_state(self, raw_input):
        return {
            "raw_input": raw_input,
            "input_type": "text",
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

    def test_clear_bug_report_is_valid(self):
        state = self._make_state(
            "The login button on the checkout page is unresponsive on Safari 17. Works on Chrome."
        )
        result = intake_agent(state)
        assert result["parsed_ticket"].is_valid is True
        assert len(result["parsed_ticket"].title) > 0

    def test_vague_input_needs_clarification(self):
        state = self._make_state("it's broken")
        result = intake_agent(state)
        assert result["parsed_ticket"].is_valid is False
        assert result["decision"] == "needs_clarification"
        assert result["parsed_ticket"].clarification_reason is not None

    def test_single_word_input(self):
        state = self._make_state("help")
        result = intake_agent(state)
        assert result["parsed_ticket"].is_valid is False

    def test_detailed_report_extracts_environment(self):
        state = self._make_state(
            "On macOS Sonoma with Safari 17.2, clicking the checkout button does nothing. "
            "Steps: 1) Add item to cart 2) Go to checkout 3) Click pay button. "
            "Console shows a TypeError."
        )
        result = intake_agent(state)
        pt = result["parsed_ticket"]
        assert pt.is_valid is True
        assert pt.environment is not None

    def test_feature_request_is_valid(self):
        state = self._make_state(
            "It would be great if the dashboard supported dark mode. "
            "Many users have requested this in our feedback channel."
        )
        result = intake_agent(state)
        assert result["parsed_ticket"].is_valid is True

    def test_trace_is_populated(self):
        state = self._make_state("Login button broken on Safari")
        result = intake_agent(state)
        assert len(result["trace"]) > 0
        assert "INTAKE" in result["trace"][0]
