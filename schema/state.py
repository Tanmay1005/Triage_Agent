from typing import Optional, TypedDict
from schema.ticket import ParsedTicket, LabeledTicket, TeamAssignment, DedupResult, JiraPayload
from schema.enums import TriageDecision, InputType


class TriageState(TypedDict):
    # Input
    raw_input: str
    input_type: InputType

    # Normalizer output (V2)
    normalized_text: Optional[str]

    # Intake output
    parsed_ticket: Optional[ParsedTicket]

    # Dedup output
    dedup_result: Optional[DedupResult]

    # Labeler output
    labeled_ticket: Optional[LabeledTicket]

    # Router output
    team_assignment: Optional[TeamAssignment]

    # Final output
    jira_payload: Optional[JiraPayload]
    decision: Optional[TriageDecision]

    # Metadata
    error: Optional[str]
    trace: list[str]  # Logs each agent's action for observability
