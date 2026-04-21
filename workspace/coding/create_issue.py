from github import Github

# Variables for authentication and repository
token = 'your_github_token_here'  # Replace with your GitHub personal access token
repository_name = 'your_username/your_repository'  # Replace with your repo, e.g. 'octocat/Hello-World'

# Authenticate and get repository
g = Github(token)
repo = g.get_repo(repository_name)

# Create a new issue
title = 'New Issue'
body = 'This is the body of the new issue.'

try:
    issue = repo.create_issue(title=title, body=body)
    print(f"Successfully created issue: {issue.html_url}")
except Exception as e:
    print(f"Failed to create issue: {e}")
