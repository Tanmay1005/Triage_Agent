import base64
import os
import requests
from dotenv import load_dotenv
from schema.ticket import JiraCreateResult

load_dotenv()


def create_jira_ticket(payload: dict) -> JiraCreateResult:
    """Create a ticket in Jira Cloud and return the ticket URL."""
    jira_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not all([jira_url, email, token]):
        return JiraCreateResult(
            success=False,
            error="Jira credentials not configured. Set JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in .env",
        )

    # Strip trailing slash from URL
    jira_url = jira_url.rstrip("/")

    auth = base64.b64encode(f"{email}:{token}".encode()).decode()

    try:
        response = requests.post(
            f"{jira_url}/rest/api/3/issue",
            json=payload,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

        if response.status_code == 201:
            data = response.json()
            key = data["key"]
            return JiraCreateResult(
                success=True,
                key=key,
                url=f"{jira_url}/browse/{key}",
            )
        else:
            return JiraCreateResult(
                success=False,
                error=f"Jira API returned {response.status_code}: {response.text}",
            )

    except requests.RequestException as e:
        return JiraCreateResult(
            success=False,
            error=f"Failed to connect to Jira: {str(e)}",
        )
