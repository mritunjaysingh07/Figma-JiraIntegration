import logging
from typing import Dict, Any
from src.config import Settings
from src.services.jira_service import JiraService
from src.services.gitlab_service import GitLabService
from loguru import logger

class WebhookHandler:
    def __init__(self, jira_service: JiraService, gitlab_service: GitLabService, figma_service, settings: Settings):
        self.jira = jira_service
        self.gitlab = gitlab_service
        self.figma_service = figma_service  # <-- Add this line
        self.settings = settings

    async def handle_jira_webhook(self, payload: Dict[str, Any], design_elements=None) -> Dict[str, Any]:
        """Handle incoming Jira webhook"""
        try:
            # Extract issue details
            issue_key = payload.get("issue", {}).get("key")
            if issue_key:
                # Update or comment on existing issue
                issue = self.jira.get_issue(issue_key)
                # ...update logic...
            else:
                # No issue key: create a new story
                # Extract design info from payload
                design_id = payload.get("design_id")
                pdf_path = payload.get("pdf_path")
                # Fetch design elements (from Figma or PDF)
                design_elements = None
                if design_id:
                    design_elements = self.figma_service.fetch_design(design_id=design_id)
                elif pdf_path:
                    design_elements = self.figma_service.fetch_design(pdf_path=pdf_path)
                # Compose summary/description from design_elements as needed
                summary = "Auto-generated story from design"
                description = str(design_elements)
                # Create the story
                issue = self.jira_service.create_story(summary, description)
                return {"status": "created", "issue_key": issue.key}

            # Get full issue details from Jira
            issue = self.jira.get_issue(issue_key)
            
            # Create branch name
            branch_name = self._generate_branch_name(issue)
            
            # Check if branch already exists
            existing_branch = self.gitlab.get_branch(branch_name)
            if existing_branch:
                logger.info(f"Branch {branch_name} already exists")
                return {"status": "success", "message": "Branch already exists", "branch": existing_branch}

            # Create new branch
            branch = self.gitlab.create_branch(branch_name)
            
            # Generate scaffold files based on issue type
            scaffold_files = self._generate_scaffold_files(issue)
            if scaffold_files:
                self.gitlab.scaffold_files(branch_name, scaffold_files)
            
            # Create merge request with AI prompt
            mr_description = self._generate_mr_description(issue)
            mr = self.gitlab.create_merge_request(
                source_branch=branch_name,
                target_branch=self.settings.DEFAULT_BRANCH,
                title=f"{issue_key}: {issue['summary']}",
                description=mr_description
            )
            
            # Add GitLab links to Jira issue
            self._update_jira_with_gitlab_links(issue_key, branch, mr)
            
            logger.info("Handling Jira webhook with payload and design elements.")
            # Implement your logic to create Jira stories from design_elements
            # Example:
            # for element in design_elements:
            #     self.jira_service.create_story(...)
            
            return {
                "status": "success",
                "branch": branch,
                "merge_request": mr
            }
            
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise

    def _generate_branch_name(self, issue: Dict[str, Any]) -> str:
        """Generate GitLab branch name from issue"""
        # Sanitize summary for branch name
        summary = issue['summary'].lower()
        summary = ''.join(c if c.isalnum() else '-' for c in summary)
        summary = '-'.join(filter(None, summary.split('-')))
        
        return f"{self.settings.BRANCH_PREFIX}/{issue['key']}-{summary}"

    def _generate_scaffold_files(self, issue: Dict[str, Any]) -> Dict[str, str]:
        """Generate scaffold files based on issue type"""
        files = {}
        
        # Add README with issue details
        files['README.md'] = f"""# {issue['summary']}

Issue: [{issue['key']}]({self.settings.JIRA_URL}/browse/{issue['key']})

## Description
{issue['description'] or 'No description provided.'}

## Components
{', '.join(issue['components']) if issue['components'] else 'No components specified.'}

## Labels
{', '.join(issue['labels']) if issue['labels'] else 'No labels specified.'}
"""
        
        return files

    def _generate_mr_description(self, issue: Dict[str, Any]) -> str:
        """Generate AI-friendly merge request description optimized for GitLab Duo"""
        # Sample usage with a mock issue:
        # sample_issue = {
        #     'key': 'PROJ-123',
        #     'summary': 'Implement User Authentication API',
        #     'description': '''
        #     Implement a secure user authentication API with the following features:
        #     - Email and password-based authentication
        #     - JWT token generation and validation
        #     - Password reset functionality
        #     - Rate limiting for failed attempts
        #     - Account lockout after multiple failed attempts
        #     ''',
        #     'issue_type': 'Feature',
        #     'priority': 'High',
        #     'components': ['Backend', 'Security'],
        #     'labels': ['api', 'auth', 'security']
        # }
        
        return f"""# 🤖 AI Development Task

## 📋 Task Overview
- **Issue**: [{issue['key']}]({self.settings.JIRA_URL}/browse/{issue['key']})
- **Type**: {issue['issue_type']}
- **Priority**: {issue.get('priority', 'Not specified')}
- **Components**: {', '.join(issue['components']) if issue['components'] else 'None'}

## 🎯 Requirements
{issue['description'] or 'No description provided.'}

## 💻 Technical Specifications
### Expected Input/Output
```yaml
input:
  # For authentication endpoint
  auth:
    type: object
    required: true
    properties:
      email:
        type: string
        format: email
        required: true
      password:
        type: string
        minLength: 8
        required: true
  
  # For password reset
  reset:
    type: object
    properties:
      email:
        type: string
        format: email
        required: true

output:
  success:
    type: object
    properties:
      status: 
        type: string
        enum: [success]
      data:
        type: object
        properties:
          token: string  # JWT token
          expiresIn: number
  error:
    type: object
    properties:
      status:
        type: string
        enum: [error]
      message: string
      code: number
```

### Technical Constraints
- Language/Framework: {', '.join(issue['components']) if issue['components'] else '[Specify framework]'}
- Performance Requirements: Response time < 200ms
- Security Considerations: OWASP Top 10 compliance required
- Scalability Needs: Support 1000+ concurrent users

## 🏗️ Implementation Guidelines
1. **Architecture**
   - Follow SOLID principles
   - Use dependency injection where appropriate
   - Implement proper error handling
   - Use repository pattern for data access

2. **Code Structure**
   - Organize code into logical modules
   - Keep functions/methods focused and single-responsibility
   - Use meaningful variable and function names
   - Follow RESTful API best practices

3. **Testing Requirements**
   - Unit tests for core functionality
   - Integration tests for API endpoints
   - Edge case coverage
   - Error scenario handling
   - Test coverage > 80%

4. **Documentation**
   - API documentation using OpenAPI/Swagger
   - Code comments for complex logic
   - Update README with setup instructions
   - Include API usage examples

## ✅ Acceptance Criteria
```gherkin
Feature: User Authentication

Scenario: Successful Login
  Given a registered user with email "user@example.com"
  When they submit valid credentials
  Then they receive a valid JWT token
  And the response includes token expiration time

Scenario: Failed Login
  Given a user with email "user@example.com"
  When they submit invalid credentials
  Then they receive an error response
  And the failed attempt is logged
  And after 5 failed attempts the account is locked

Scenario: Password Reset
  Given a registered user with email "user@example.com"
  When they request a password reset
  Then they receive a reset link via email
  And the reset link expires after 1 hour
```

## 🔍 Review Checklist
- [ ] Code follows project standards and patterns
- [ ] Unit tests are comprehensive and passing
- [ ] Integration tests added where needed
- [ ] Error handling is robust
- [ ] Documentation is complete and clear
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Logging and monitoring added
- [ ] Code is properly typed/documented
- [ ] Dependencies are properly managed

## 🛠️ Technical Notes
- **Dependencies**: 
  - JWT library for token management
  - Password hashing library (bcrypt)
  - Rate limiting middleware
  - Email service integration

- **Configuration**: 
  - JWT secret and expiration
  - Rate limiting rules
  - Email service credentials
  - Password policy settings

- **Database**: 
  - User schema updates
  - Token blacklist table
  - Failed attempts tracking

- **APIs**: 
  - POST /api/auth/login
  - POST /api/auth/refresh
  - POST /api/auth/reset-password
  - POST /api/auth/change-password

## 🔐 Security Considerations
- [ ] Password hashing using bcrypt
- [ ] JWT token with appropriate expiration
- [ ] Rate limiting for all endpoints
- [ ] Input validation and sanitization
- [ ] XSS and CSRF protection
- [ ] Secure password reset flow
- [ ] Audit logging for security events

## 📝 Additional Context
This merge request was automatically created by the GitLab Code Assistant Agent. GitLab Duo will use this structured format to generate appropriate code suggestions.

## 🤖 AI Instructions
@GitLab-Duo please:
1. Generate code following the above specifications
2. Implement secure authentication flows
3. Add comprehensive test suite
4. Include API documentation
5. Follow REST API best practices
6. Implement proper error handling and logging
7. Consider rate limiting and security measures"""

    def _update_jira_with_gitlab_links(self, issue_key: str, branch: Dict[str, Any], mr: Dict[str, Any]) -> None:
        """Update Jira issue with GitLab links"""
        comment = f"""GitLab resources created:
* Branch: [{branch['name']}]({branch['web_url']})
* Merge Request: [!{mr['id']}]({mr['web_url']})"""
        
        self.jira.add_comment(issue_key, comment)