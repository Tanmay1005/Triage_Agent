from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"   # System down, data loss, security breach
    HIGH = "high"           # Major feature broken, no workaround
    MEDIUM = "medium"       # Feature broken, workaround exists
    LOW = "low"             # Minor issue, cosmetic, enhancement


class Priority(str, Enum):
    P0 = "P0"  # Drop everything
    P1 = "P1"  # Next sprint
    P2 = "P2"  # Backlog - soon
    P3 = "P3"  # Backlog - eventually


class IssueType(str, Enum):
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    IMPROVEMENT = "improvement"
    TASK = "task"
    INCIDENT = "incident"


class TriageDecision(str, Enum):
    CREATE_TICKET = "create_ticket"
    DUPLICATE = "duplicate"
    NEEDS_CLARIFICATION = "needs_clarification"


class InputType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
