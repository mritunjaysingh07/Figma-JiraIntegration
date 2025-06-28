from jira import JIRA
from loguru import logger

class JiraService:
    def __init__(self, config):
        self.project_key = config.get("project_key")
        self.fields = config.get("fields", {})
        self.url = config.get("url")
        self.email = config.get("email")
        self.api_token = config.get("api_token")
        if self.url and self.email and self.api_token:
            options = {"server": self.url}
            self.client = JIRA(options=options, basic_auth=(self.email, self.api_token))
        else:
            logger.warning("Jira credentials not fully provided. Client not initialized.")
            self.client = None

    def create_epic(self, summary, description):
        if not self.client:
            raise RuntimeError("Jira client is not initialized.")
        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Epic"},
            self.fields.get("epic_name", "customfield_10011"): summary
        }
        issue = self.client.create_issue(fields=fields)
        logger.info(f"Created Jira epic: {issue.key}")
        return issue.key

    def create_story(self, summary, description, story_points=None, epic_link=None, extra_fields=None):
        if not self.client:
            raise RuntimeError("Jira client is not initialized.")
        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Story"},
        }
        if story_points and self.fields.get("story_points"):
            fields[self.fields["story_points"]] = story_points
        if epic_link and self.fields.get("epic_link"):
            fields[self.fields["epic_link"]] = epic_link

        # Handle acceptance criteria and technical requirements
        ac = None
        tr = None
        if extra_fields:
            # Remove 'priority' and 'description' if present
            extra_fields = {k: v for k, v in extra_fields.items() if k.lower() not in ["priority", "description"]}
            # Extract acceptance criteria and technical requirements if present
            ac = extra_fields.pop("acceptance_criteria", None)
            tr = extra_fields.pop("technical_requirements", None)
            fields.update(extra_fields)

        # Append acceptance criteria and technical requirements to description if present
        if ac:
            fields["description"] += "\n\nh3. Acceptance Criteria\n"
            if isinstance(ac, list):
                for item in ac:
                    fields["description"] += f"- {item}\n"
            else:
                fields["description"] += f"{ac}\n"
        if tr:
            fields["description"] += "\n\nh3. Technical Requirements\n"
            if isinstance(tr, list):
                for item in tr:
                    fields["description"] += f"- {item}\n"
            else:
                fields["description"] += f"{tr}\n"

        logger.info(f"Jira Story Description:\n{fields['description']}")
        logger.info(f"Extra fields passed: {extra_fields}")
        issue = self.client.create_issue(fields=fields)
        logger.info(f"Created Jira story: {issue.key}")
        return issue.key

    def get_issue(self, issue_key):
        """
        Fetch a Jira issue by its key.
        """
        if not self.client:
            raise RuntimeError("Jira client is not initialized.")
        try:
            return self.client.issue(issue_key)
        except Exception as e:
            logger.error(f"Failed to fetch Jira issue {issue_key}: {e}")
            raise

    # Add more methods as needed for your workflow (update, search, etc.)