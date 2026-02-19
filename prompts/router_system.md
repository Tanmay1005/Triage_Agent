# Router Agent — Routing Logic Reference

The router agent is deterministic (no LLM). It assigns tickets to teams by matching
ticket labels and component against each team's skills matrix.

## Algorithm

1. Collect signals: ticket labels + component (lowercased)
2. For each team, count how many of its skills overlap with signals
3. Apply capacity penalty: score -= 0.1 * max(0, 5 - capacity)
4. Highest scoring team wins
5. On no match, default to "platform" team for triage

## Teams

See data/team_skills.json for the full mapping.
