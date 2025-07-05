import os
import git

def fetch_docs(query: str, repo_url="https://github.com/langchain-ai/langchain.git", clone_dir="data/langchain_repo") -> list:
    """
    Clones a GitHub repository and reads markdown files.
    """
    docs = []
    try:
        if not os.path.exists(clone_dir):
            print(f"Cloning repository: {repo_url}")
            git.Repo.clone_from(repo_url, clone_dir)
        else:
            print("Repository already cloned.")

        for root, _, files in os.walk(clone_dir):
            for file in files:
                if file.endswith(".md"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        docs.append({"source": filepath, "content": f.read()})
    except Exception as e:
        print(f"An error occurred while fetching from GitHub: {e}")
    
    return docs
