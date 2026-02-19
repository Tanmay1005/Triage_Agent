# Sentinel — Autonomous Jira Triage Agent

A multi-agent LangGraph pipeline that autonomously triages bug reports: parsing raw text into structured tickets, detecting duplicates via vector similarity, classifying severity/priority/type, and routing to the correct team — with live Jira Cloud integration.

## Architecture

```
Raw Input
  |
  +-- Too vague? ----------> Return "Clarification Needed" + suggestions
  |
  +-- Valid? --> Duplicate? -> Return "Duplicate" + link to existing ticket
  |                |
  |                NO
  |                v
  |            Label --> Route --> Jira Payload --> [Create in Jira]
```

### Pipeline Agents

| Agent | Purpose | LLM? |
|-------|---------|------|
| **Intake** | Parse raw text into structured `ParsedTicket` | Claude Haiku |
| **Dedup** | Semantic similarity search against existing tickets | Local embeddings |
| **Labeler** | Classify severity, priority, issue type, labels | Claude Haiku |
| **Router** | Match ticket to team via skills matrix | Deterministic |
| **Jira Client** | Create ticket in Jira Cloud | API call |

### Tech Stack

- **Orchestration:** LangGraph (stateful graph with conditional routing)
- **LLM:** Claude Haiku 4.5 via Anthropic SDK
- **Vector Store:** ChromaDB (in-process, cosine similarity)
- **Embeddings:** `all-MiniLM-L6-v2` (sentence-transformers, runs locally)
- **Frontend:** Gradio
- **Structured Output:** Pydantic V2
- **Testing:** pytest + custom eval harness

### Cost Per Triage: ~$0.003

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys:
#   GOOGLE_API_KEY=sk-ant-...
#   JIRA_URL=https://your-instance.atlassian.net  (optional)
#   JIRA_EMAIL=you@email.com                       (optional)
#   JIRA_API_TOKEN=...                              (optional)
#   JIRA_PROJECT_KEY=ENG                            (optional)
```

### 3. Jira Setup (Optional)

1. Create a free Jira Cloud instance at [atlassian.com](https://www.atlassian.com)
2. Create a project (e.g., `ENG`)
3. Generate an API token at [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
4. Add credentials to `.env`

The app works without Jira credentials — it just won't create real tickets.

### 4. Launch

```bash
python app.py
```

Opens Gradio UI at `http://localhost:7860`.

## Usage

1. **Paste a bug report** into the text box
2. **Click "Run Triage"** — results populate across 5 tabs:
   - Intake Parse (structured ticket)
   - Dedup Check (duplicate detection)
   - Labels & Severity (classification)
   - Routing & Jira Payload (team assignment)
   - Pipeline Trace (step-by-step log)
3. **Click "Create in Jira"** (if available) to create a real ticket

## Testing

```bash
# Unit tests only (fast, no LLM calls)
pytest tests/ -m "not llm" -v

# All tests including LLM tests
pytest tests/ -v

# Eval suite (55 test cases)
python -m eval.runner
```

## Project Structure

```
├── agents/
│   ├── intake.py          # Parse raw text -> ParsedTicket
│   ├── dedup.py           # Semantic duplicate detection (ChromaDB)
│   ├── labeler.py         # Severity/priority/type classification
│   ├── router.py          # Team assignment via skills matrix
│   └── jira_client.py     # Jira Cloud API integration
├── schema/
│   ├── enums.py           # Severity, Priority, IssueType enums
│   ├── ticket.py          # Pydantic V2 data models
│   └── state.py           # LangGraph state definition
├── graph/
│   └── pipeline.py        # LangGraph workflow (conditional routing)
├── data/
│   ├── team_skills.json   # Team -> skills mapping
│   └── seed_tickets.json  # 50 synthetic tickets for ChromaDB
├── eval/
│   ├── test_cases.json    # 55 labeled eval cases
│   ├── runner.py          # Eval execution engine
│   └── metrics.py         # Accuracy/precision calculations
├── tests/                 # pytest suite
├── prompts/               # Externalized LLM prompts
└── app.py                 # Gradio UI entry point
```
