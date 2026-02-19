import pytest
import json
from schema.ticket import ParsedTicket, LabeledTicket, DedupResult, TeamAssignment
from schema.enums import Severity, Priority, IssueType


@pytest.fixture
def valid_parsed_ticket():
    return ParsedTicket(
        title="Login button unresponsive on Safari - Checkout page",
        description="Users on Safari 17+ cannot click the login button on the checkout page.",
        component="checkout",
        steps_to_reproduce="1. Go to checkout page on Safari 17. 2. Click login button. 3. Nothing happens.",
        environment="Safari 17.2, macOS Sonoma",
        reporter_context=None,
        is_valid=True,
        clarification_reason=None,
    )


@pytest.fixture
def invalid_parsed_ticket():
    return ParsedTicket(
        title="",
        description="",
        component=None,
        steps_to_reproduce=None,
        environment=None,
        reporter_context=None,
        is_valid=False,
        clarification_reason="Input is too vague. Please specify what is broken and where.",
    )


@pytest.fixture
def labeled_ticket_high():
    return LabeledTicket(
        severity=Severity.HIGH,
        priority=Priority.P1,
        issue_type=IssueType.BUG,
        labels=["safari", "checkout", "ui", "login"],
        confidence=0.92,
    )


@pytest.fixture
def labeled_ticket_critical():
    return LabeledTicket(
        severity=Severity.CRITICAL,
        priority=Priority.P0,
        issue_type=IssueType.INCIDENT,
        labels=["security", "passwords", "api", "pii"],
        confidence=0.98,
    )


@pytest.fixture
def team_skills():
    with open("data/team_skills.json") as f:
        return json.load(f)


@pytest.fixture
def sample_state_valid(valid_parsed_ticket, labeled_ticket_high):
    return {
        "raw_input": "Login button unresponsive on Safari checkout page",
        "input_type": "text",
        "normalized_text": None,
        "parsed_ticket": valid_parsed_ticket,
        "dedup_result": None,
        "labeled_ticket": labeled_ticket_high,
        "team_assignment": None,
        "jira_payload": None,
        "decision": None,
        "error": None,
        "trace": [],
    }


@pytest.fixture
def sample_state_invalid():
    return {
        "raw_input": "it's broken",
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
