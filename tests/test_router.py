import pytest
from agents.router import router_agent, load_team_skills
from schema.ticket import ParsedTicket, LabeledTicket
from schema.enums import Severity, Priority, IssueType


class TestRouterAgent:
    def _make_state(self, component, labels):
        return {
            "raw_input": "test",
            "input_type": "text",
            "normalized_text": None,
            "parsed_ticket": ParsedTicket(
                title="Test", description="Test", component=component, is_valid=True
            ),
            "dedup_result": None,
            "labeled_ticket": LabeledTicket(
                severity=Severity.HIGH,
                priority=Priority.P1,
                issue_type=IssueType.BUG,
                labels=labels,
                confidence=0.9,
            ),
            "team_assignment": None,
            "jira_payload": None,
            "decision": None,
            "error": None,
            "trace": [],
        }

    def test_routes_to_frontend_for_browser_issues(self):
        state = self._make_state("checkout", ["safari", "ui", "login"])
        result = router_agent(state)
        assert result["team_assignment"].team == "frontend"

    def test_routes_to_payments_for_stripe(self):
        state = self._make_state("payments", ["stripe", "checkout", "billing"])
        result = router_agent(state)
        assert result["team_assignment"].team == "payments"

    def test_routes_to_security_for_xss(self):
        state = self._make_state("security", ["xss", "vulnerability"])
        result = router_agent(state)
        assert result["team_assignment"].team == "security"

    def test_routes_to_data_for_analytics(self):
        state = self._make_state("analytics", ["dashboard", "export", "csv"])
        result = router_agent(state)
        assert result["team_assignment"].team == "data"

    def test_routes_to_platform_for_auth(self):
        state = self._make_state("auth", ["login", "sso", "api"])
        result = router_agent(state)
        assert result["team_assignment"].team == "platform"

    def test_fallback_to_platform_for_unknown(self):
        state = self._make_state("unknown_system", ["something_random"])
        result = router_agent(state)
        assert result["team_assignment"].team == "platform"

    def test_jira_payload_structure(self):
        state = self._make_state("checkout", ["safari", "ui"])
        result = router_agent(state)
        payload = result["jira_payload"]
        assert "project" in payload.fields
        assert "summary" in payload.fields
        assert "issuetype" in payload.fields
        assert "priority" in payload.fields
        assert "assignee" in payload.fields

    def test_jira_payload_has_labels(self):
        state = self._make_state("checkout", ["safari", "ui"])
        result = router_agent(state)
        assert result["jira_payload"].fields["labels"] == ["safari", "ui"]

    def test_jira_payload_has_components(self):
        state = self._make_state("checkout", ["safari"])
        result = router_agent(state)
        assert result["jira_payload"].fields["components"] == [{"name": "checkout"}]

    def test_jira_payload_no_components_when_none(self):
        state = self._make_state(None, ["safari", "ui"])
        result = router_agent(state)
        assert result["jira_payload"].fields["components"] == []

    def test_decision_is_create_ticket(self):
        state = self._make_state("checkout", ["safari"])
        result = router_agent(state)
        assert result["decision"] == "create_ticket"

    def test_trace_is_appended(self):
        state = self._make_state("payments", ["stripe"])
        state["trace"] = ["PREVIOUS_STEP"]
        result = router_agent(state)
        assert len(result["trace"]) == 2
        assert "ROUTER:" in result["trace"][1]

    def test_assignee_is_team_lead(self):
        state = self._make_state("security", ["xss", "vulnerability"])
        result = router_agent(state)
        assert result["team_assignment"].assignee == "eve_johnson"

    def test_reasoning_includes_matched_skills(self):
        state = self._make_state("payments", ["stripe", "billing"])
        result = router_agent(state)
        assert "Matched skills:" in result["team_assignment"].reasoning


class TestTeamSkillsMatrix:
    def test_all_teams_have_required_fields(self):
        teams = load_team_skills()
        for name, info in teams.items():
            assert "lead" in info, f"{name} missing lead"
            assert "skills" in info, f"{name} missing skills"
            assert "capacity" in info, f"{name} missing capacity"
            assert isinstance(info["skills"], list)
            assert info["capacity"] > 0

    def test_five_teams_exist(self):
        teams = load_team_skills()
        assert len(teams) == 5
        assert "payments" in teams
        assert "platform" in teams
        assert "frontend" in teams
        assert "data" in teams
        assert "security" in teams

    def test_each_team_has_skills(self):
        teams = load_team_skills()
        for name, info in teams.items():
            assert len(info["skills"]) >= 3, f"{name} has too few skills"
