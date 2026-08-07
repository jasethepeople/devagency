"""
Linear GraphQL API Client — full ticket lifecycle integration.

Provides create, read, update, and comment operations against
the Linear project management platform via its GraphQL API.
"""
import requests
from typing import Any, Optional

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

LINEAR_API_URL = "https://api.linear.app/graphql"


class LinearClient:
    """
    Linear GraphQL API client for issue management.
    Supports create, comment, update status, and fetch operations.
    """

    def __init__(self):
        self.api_key = Config.LINEAR_API_KEY
        self.team_id = Config.LINEAR_TEAM_ID
        if not self.api_key:
            logger.warning("LINEAR_API_KEY not set — Linear integration disabled")
        if not self.team_id:
            logger.warning("LINEAR_TEAM_ID not set — issue creation may fail")

    def _query(self, query: str, variables: dict | None = None) -> dict[str, Any]:
        """
        Execute a GraphQL query/mutation against Linear API.

        Args:
            query: GraphQL query string
            variables: Optional variables dict

        Returns:
            JSON response dict
        """
        if not self.api_key:
            logger.error("Linear API key not configured")
            return {"errors": [{"message": "No API key"}]}

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"query": query, "variables": variables or {}}

        try:
            resp = requests.post(LINEAR_API_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                logger.error(f"Linear GraphQL errors: {data['errors']}")
            return data
        except requests.RequestException as e:
            logger.error(f"Linear API request failed: {e}")
            return {"errors": [{"message": str(e)}]}

    def create_issue(
        self,
        title: str,
        description: str,
        label: str,
        assignee: Optional[str] = None,
    ) -> str:
        """
        Create a new Linear issue.

        Args:
            title: Issue title
            description: Issue description (markdown supported)
            label: Agent label (e.g., "codex", "claude", "local")
            assignee: Optional user ID to assign

        Returns:
            Created issue ID
        """
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    url
                }
            }
        }
        """
        variables = {
            "input": {
                "title": title,
                "description": description,
                "teamId": self.team_id,
                "labelIds": [label] if label else [],
            }
        }
        if assignee:
            variables["input"]["assigneeId"] = assignee

        result = self._query(mutation, variables)
        issue_data = result.get("data", {}).get("issueCreate", {})
        if issue_data.get("success"):
            issue_id = issue_data["issue"]["id"]
            logger.info(f"Created Linear issue: {issue_data['issue']['identifier']} ({issue_id})")
            return issue_id
        else:
            logger.error(f"Failed to create issue: {result}")
            return ""

    def comment(self, issue_id: str, body: str) -> bool:
        """
        Add a comment to an existing issue.

        Args:
            issue_id: Linear issue ID
            body: Comment text (markdown supported)

        Returns:
            True if successful
        """
        mutation = """
        mutation CreateComment($input: CommentCreateInput!) {
            commentCreate(input: $input) {
                success
                comment {
                    id
                }
            }
        }
        """
        variables = {
            "input": {
                "issueId": issue_id,
                "body": body,
            }
        }
        result = self._query(mutation, variables)
        success = result.get("data", {}).get("commentCreate", {}).get("success", False)
        if success:
            logger.info(f"Commented on issue {issue_id}")
        else:
            logger.error(f"Failed to comment: {result}")
        return success

    def update_status(self, issue_id: str, state_id: str) -> bool:
        """
        Move an issue to a specific workflow state.

        Args:
            issue_id: Linear issue ID
            state_id: Target state ID (e.g., "Done", "In Progress")

        Returns:
            True if successful
        """
        mutation = """
        mutation UpdateIssueState($id: String!, $stateId: String!) {
            issueUpdate(id: $id, input: { stateId: $stateId }) {
                success
                issue {
                    id
                    state {
                        name
                    }
                }
            }
        }
        """
        variables = {"id": issue_id, "stateId": state_id}
        result = self._query(mutation, variables)
        success = result.get("data", {}).get("issueUpdate", {}).get("success", False)
        if success:
            state_name = result.get("data", {}).get("issueUpdate", {}).get("issue", {}).get("state", {}).get("name", "?")
            logger.info(f"Issue {issue_id} moved to: {state_name}")
        else:
            logger.error(f"Failed to update status: {result}")
        return success

    def fetch_issues(
        self,
        assignee: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Fetch issues with optional filtering.

        Args:
            assignee: Filter by assignee user ID
            state: Filter by state name (e.g., "In Progress")
            limit: Max results to return

        Returns:
            List of issue dicts
        """
        query = """
        query Issues($filter: IssueFilter, $first: Int) {
            issues(filter: $filter, first: $first) {
                nodes {
                    id
                    identifier
                    title
                    description
                    state {
                        name
                    }
                    assignee {
                        name
                    }
                    labels {
                        nodes {
                            name
                        }
                    }
                    url
                }
            }
        }
        """
        filter_dict: dict[str, Any] = {}
        if assignee:
            filter_dict["assignee"] = {"id": {"eq": assignee}}
        if state:
            filter_dict["state"] = {"name": {"eq": state}}

        variables = {"filter": filter_dict, "first": limit}
        result = self._query(query, variables)
        issues = result.get("data", {}).get("issues", {}).get("nodes", [])
        logger.info(f"Fetched {len(issues)} issues from Linear")
        return issues

    def get_team_states(self) -> list[dict[str, Any]]:
        """
        Fetch available workflow states for the configured team.

        Returns:
            List of state dicts with id and name
        """
        query = """
        query TeamStates($id: String!) {
            team(id: $id) {
                states {
                    nodes {
                        id
                        name
                        type
                    }
                }
            }
        }
        """
        variables = {"id": self.team_id}
        result = self._query(query, variables)
        states = result.get("data", {}).get("team", {}).get("states", {}).get("nodes", [])
        return states
