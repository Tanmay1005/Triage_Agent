from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from schema.enums import Severity, Priority, IssueType


class ParsedTicket(BaseModel):
    """Output of the Intake Agent — extracted fields from raw input."""
    title: str = Field(..., max_length=200, description="Concise ticket title")
    description: str = Field(..., description="Detailed description of the issue")
    component: Optional[str] = Field(None, description="Affected system component")
    steps_to_reproduce: Optional[str] = Field(None, description="Steps to reproduce if applicable")
    environment: Optional[str] = Field(None, description="Browser, OS, device info if mentioned")
    reporter_context: Optional[str] = Field(None, description="Any context about who reported this")
    is_valid: bool = Field(..., description="False if input is too vague to create a ticket")
    clarification_reason: Optional[str] = Field(None, description="Why clarification is needed, if is_valid=False")


class LabeledTicket(BaseModel):
    """Output of the Labeler Agent — classification fields added."""
    severity: Severity
    priority: Priority
    issue_type: IssueType
    labels: list[str] = Field(default_factory=list, description="Relevant tags: e.g. ['safari', 'checkout', 'ui']")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence in classification")


class TeamAssignment(BaseModel):
    """Output of the Router Agent — who handles this ticket."""
    team: str = Field(..., description="Team name from skills matrix")
    assignee: str = Field(..., description="Team lead or available engineer")
    reasoning: str = Field(..., description="Why this team was selected")


class JiraPayload(BaseModel):
    """Final output — Jira API V3 compatible payload."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fields": {
                    "project": {"key": "ENG"},
                    "summary": "Login button unresponsive on Safari - Checkout page",
                    "issuetype": {"name": "Bug"},
                    "priority": {"name": "High"},
                    "labels": ["safari", "checkout", "ui"],
                    "assignee": {"accountId": "alice_payments"},
                }
            }
        }
    )

    fields: dict = Field(..., description="Jira-compatible fields object")


class DedupResult(BaseModel):
    """Output of the Dedup Agent."""
    is_duplicate: bool
    similar_ticket_id: Optional[str] = None
    similar_ticket_title: Optional[str] = None
    similarity_score: Optional[float] = None


class JiraCreateResult(BaseModel):
    """Result of creating a ticket in Jira Cloud."""
    success: bool
    key: Optional[str] = None       # e.g. "ENG-42"
    url: Optional[str] = None       # e.g. "https://instance.atlassian.net/browse/ENG-42"
    error: Optional[str] = None
