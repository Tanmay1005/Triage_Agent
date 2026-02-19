import json
import os
from schema.ticket import TeamAssignment, JiraPayload
from schema.state import TriageState

_SKILLS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "team_skills.json")


def load_team_skills() -> dict:
    with open(_SKILLS_PATH) as f:
        return json.load(f)


def router_agent(state: TriageState) -> dict:
    """Route ticket to the correct team based on skills matrix and labels."""
    parsed = state["parsed_ticket"]
    labeled = state["labeled_ticket"]
    teams = load_team_skills()

    # Score each team based on keyword overlap with ticket labels + component
    ticket_signals = set(labeled.labels)
    if parsed.component:
        ticket_signals.add(parsed.component.lower())

    team_scores = {}
    for team_name, info in teams.items():
        overlap = ticket_signals.intersection(set(info["skills"]))
        # Weight by overlap count, penalize full teams slightly
        score = len(overlap) - (0.1 * max(0, 5 - info["capacity"]))
        team_scores[team_name] = (score, overlap)

    # Pick the best match
    best_team = max(team_scores, key=lambda t: team_scores[t][0])
    best_score, matched_skills = team_scores[best_team]
    team_info = teams[best_team]

    # Fallback if no skills matched
    if best_score <= 0:
        best_team = "platform"
        team_info = teams["platform"]
        reasoning = "No strong skill match found; defaulting to platform team for triage."
        matched_skills = set()
    else:
        reasoning = f"Matched skills: {', '.join(sorted(matched_skills))}. Team capacity: {team_info['capacity']}."

    assignment = TeamAssignment(
        team=best_team,
        assignee=team_info["lead"],
        reasoning=reasoning,
    )

    # Build Jira API v3 compatible payload
    project_key = os.getenv("JIRA_PROJECT_KEY", "ENG")
    jira = JiraPayload(
        fields={
            "project": {"key": project_key},
            "summary": parsed.title,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": parsed.description}],
                    }
                ],
            },
            "issuetype": {"name": labeled.issue_type.value.replace("_", " ").title()},
            "priority": {"name": labeled.priority.value},
            "labels": labeled.labels,
            "assignee": {"accountId": team_info["lead"]},
            "components": [{"name": parsed.component}] if parsed.component else [],
        }
    )

    return {
        "team_assignment": assignment,
        "jira_payload": jira,
        "decision": "create_ticket",
        "trace": state.get("trace", []) + [
            f"ROUTER: Assigned to {best_team} ({team_info['lead']}) — {reasoning}"
        ],
    }
