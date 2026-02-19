import pytest
from pydantic import ValidationError
from schema.ticket import ParsedTicket, LabeledTicket, DedupResult, TeamAssignment, JiraPayload, JiraCreateResult
from schema.enums import Severity, Priority, IssueType, TriageDecision, InputType


class TestEnums:
    def test_severity_values(self):
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"

    def test_priority_values(self):
        assert Priority.P0 == "P0"
        assert Priority.P3 == "P3"

    def test_issue_type_values(self):
        assert IssueType.BUG == "bug"
        assert IssueType.FEATURE_REQUEST == "feature_request"
        assert IssueType.INCIDENT == "incident"

    def test_triage_decision_values(self):
        assert TriageDecision.CREATE_TICKET == "create_ticket"
        assert TriageDecision.DUPLICATE == "duplicate"
        assert TriageDecision.NEEDS_CLARIFICATION == "needs_clarification"

    def test_input_type_values(self):
        assert InputType.TEXT == "text"


class TestParsedTicket:
    def test_valid_ticket(self):
        ticket = ParsedTicket(
            title="Test bug",
            description="Something is broken",
            is_valid=True,
        )
        assert ticket.title == "Test bug"
        assert ticket.is_valid is True

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            ParsedTicket(
                title="x" * 201,
                description="test",
                is_valid=True,
            )

    def test_title_at_max_length(self):
        ticket = ParsedTicket(
            title="x" * 200,
            description="test",
            is_valid=True,
        )
        assert len(ticket.title) == 200

    def test_invalid_ticket_with_reason(self):
        ticket = ParsedTicket(
            title="",
            description="",
            is_valid=False,
            clarification_reason="Too vague",
        )
        assert ticket.is_valid is False
        assert ticket.clarification_reason == "Too vague"

    def test_optional_fields_default_none(self):
        ticket = ParsedTicket(title="Bug", description="Desc", is_valid=True)
        assert ticket.component is None
        assert ticket.steps_to_reproduce is None
        assert ticket.environment is None
        assert ticket.reporter_context is None
        assert ticket.clarification_reason is None

    def test_serialization_roundtrip(self):
        ticket = ParsedTicket(
            title="Test",
            description="Desc",
            component="auth",
            is_valid=True,
        )
        data = ticket.model_dump()
        restored = ParsedTicket.model_validate(data)
        assert restored == ticket

    def test_json_roundtrip(self):
        ticket = ParsedTicket(
            title="Test",
            description="Desc",
            is_valid=True,
        )
        json_str = ticket.model_dump_json()
        restored = ParsedTicket.model_validate_json(json_str)
        assert restored == ticket


class TestLabeledTicket:
    def test_valid_labeling(self):
        labeled = LabeledTicket(
            severity=Severity.HIGH,
            priority=Priority.P1,
            issue_type=IssueType.BUG,
            labels=["safari", "ui"],
            confidence=0.9,
        )
        assert labeled.severity == Severity.HIGH

    def test_confidence_upper_bound(self):
        with pytest.raises(ValidationError):
            LabeledTicket(
                severity=Severity.LOW,
                priority=Priority.P3,
                issue_type=IssueType.TASK,
                confidence=1.5,
            )

    def test_confidence_lower_bound(self):
        with pytest.raises(ValidationError):
            LabeledTicket(
                severity=Severity.LOW,
                priority=Priority.P3,
                issue_type=IssueType.TASK,
                confidence=-0.1,
            )

    def test_confidence_at_bounds(self):
        low = LabeledTicket(
            severity=Severity.LOW,
            priority=Priority.P3,
            issue_type=IssueType.TASK,
            confidence=0.0,
        )
        high = LabeledTicket(
            severity=Severity.LOW,
            priority=Priority.P3,
            issue_type=IssueType.TASK,
            confidence=1.0,
        )
        assert low.confidence == 0.0
        assert high.confidence == 1.0

    def test_empty_labels_default(self):
        labeled = LabeledTicket(
            severity=Severity.LOW,
            priority=Priority.P3,
            issue_type=IssueType.TASK,
            confidence=0.5,
        )
        assert labeled.labels == []

    def test_invalid_severity_string(self):
        with pytest.raises(ValidationError):
            LabeledTicket(
                severity="extreme",
                priority=Priority.P0,
                issue_type=IssueType.BUG,
                confidence=0.9,
            )


class TestDedupResult:
    def test_not_duplicate(self):
        result = DedupResult(is_duplicate=False)
        assert result.similar_ticket_id is None
        assert result.similar_ticket_title is None
        assert result.similarity_score is None

    def test_duplicate_with_details(self):
        result = DedupResult(
            is_duplicate=True,
            similar_ticket_id="TICK-001",
            similar_ticket_title="Login bug",
            similarity_score=0.92,
        )
        assert result.is_duplicate is True
        assert result.similarity_score == 0.92


class TestTeamAssignment:
    def test_valid_assignment(self):
        assignment = TeamAssignment(
            team="frontend",
            assignee="carol_zhang",
            reasoning="Matched skills: safari, ui",
        )
        assert assignment.team == "frontend"
        assert assignment.assignee == "carol_zhang"


class TestJiraPayload:
    def test_valid_payload(self):
        payload = JiraPayload(
            fields={
                "project": {"key": "ENG"},
                "summary": "Test",
                "issuetype": {"name": "Bug"},
            }
        )
        assert payload.fields["project"]["key"] == "ENG"

    def test_fields_required(self):
        with pytest.raises(ValidationError):
            JiraPayload()


class TestJiraCreateResult:
    def test_success_result(self):
        result = JiraCreateResult(
            success=True,
            key="ENG-42",
            url="https://example.atlassian.net/browse/ENG-42",
        )
        assert result.success is True
        assert result.key == "ENG-42"

    def test_failure_result(self):
        result = JiraCreateResult(
            success=False,
            error="Connection refused",
        )
        assert result.success is False
        assert result.error == "Connection refused"
        assert result.key is None
        assert result.url is None
