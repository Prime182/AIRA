import os
import git
import requests
from typing import List, Dict, Any

# Renamed the original fetch_docs to clone_and_read_repo_files
def clone_and_read_repo_files(repo_url: str, clone_dir: str) -> List[Dict[str, str]]:
    """
    Clones a GitHub repository and reads specified file types.
    This function is intended for the /process_github_repo endpoint.
    """
    docs = []
    try:
        if not os.path.exists(clone_dir):
            print(f"Cloning repository: {repo_url}")
            git.Repo.clone_from(repo_url, clone_dir)
        else:
            print(f"Repository already cloned at {clone_dir}. Pulling latest changes...")
            repo = git.Repo(clone_dir)
            origin = repo.remotes.origin
            origin.pull()

        # Define file extensions to parse
        file_extensions = (".md", ".py", ".js", ".ts")

        for root, _, files in os.walk(clone_dir):
            for file in files:
                if file.endswith(file_extensions):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            docs.append({"source": filepath, "content": content})
                    except Exception as e:
                        print(f"Could not read file {filepath}: {e}")
    except Exception as e:
        print(f"An error occurred while cloning/fetching from GitHub: {e}")
    
    return docs

def search_github_repos(query: str) -> List[Dict[str, Any]]:
    """
    Searches GitHub repositories based on a user's query using the GitHub REST API.
    Extracts full_name, description, html_url, default_branch, owner.login, and stargazers_count.
    """
    search_url = f"https://api.github.com/search/repositories?q={query}"
    headers = {"Accept": "application/vnd.github.v3+json"} # Recommended by GitHub API docs

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        
        repos = []
        for item in data.get("items", []):
            repos.append({
                "full_name": item.get("full_name"),
                "description": item.get("description"),
                "html_url": item.get("html_url"),
                "default_branch": item.get("default_branch"),
                "owner_login": item.get("owner", {}).get("login"),
                "stargazers_count": item.get("stargazers_count")
            })
        return repos
    except requests.exceptions.RequestException as e:
        print(f"Error searching GitHub repositories: {e}")
        return []

def fetch_readme_content(owner: str, repo: str) -> str:
    """
    Fetches the README.md content for a given GitHub repository.
    """
    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {"Accept": "application/vnd.github.v3.raw"} # To get raw content

    try:
        response = requests.get(readme_url, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching README for {owner}/{repo}: {e}")
        return f"Could not fetch README: {e}"

def fetch_docs(query: str, max_repos=3) -> List[Dict[str, str]]:
    """
    Searches GitHub repositories and fetches README content from top results.
    This function is intended for the general context fetching (e.g., by context_router).
    """
    print(f"Searching GitHub for repos with query: '{query}'")
    repos = search_github_repos(query)
    
    docs = []
    for i, repo in enumerate(repos):
        if i >= max_repos: # Limit the number of READMEs fetched
            break
        owner = repo.get("owner_login")
        repo_name = repo.get("full_name").split('/')[1] # Extract repo name from full_name
        
        if owner and repo_name:
            readme_content = fetch_readme_content(owner, repo_name)
            if readme_content and "Could not fetch README" not in readme_content:
                # Create a preview of the README content
                readme_preview = readme_content[:300] + "..." if len(readme_content) > 300 else readme_content
                docs.append({
                    "title": f"{repo.get('full_name')} by {repo.get('owner_login')}",
                    "content": f"Description: {repo.get('description', 'No description')}\n\nREADME Preview:\n{readme_preview}",
                    "source": repo.get("html_url")
                })
    return docs
