# AIRA: AI-Powered Research Agent

AIRA (AI-Powered Research Agent) is a backend system designed to facilitate research and information retrieval using Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG). It allows users to fetch context from various sources, process it, and engage in intelligent conversations powered by the Gemini LLM, with persistent chat memory.

## Features

*   **Model Context Protocol (MCP) Server:** AIRA functions as an MCP server, exposing its capabilities (context fetching, chat, GitHub integration) as tools and resources that can be accessed by other MCP-compatible agents or systems.
*   **Modular Architecture:** Clean separation of functionalities into distinct modules (`context_sources`, `modules`, `utils`).
*   **Context Fetching:**
    *   Fetch research papers from **arXiv API**.
    *   Read content from **user's local files**.
    *   Search **GitHub repositories** and fetch READMEs as context.
*   **GitHub Integration:**
    *   Search GitHub repositories based on a query.
    *   Fetch and preview `README.md` content for any GitHub repository.
    *   Process entire GitHub repositories (clone, parse `.md`, `.py`, `.js`, `.ts` files, chunk, and embed) for deep RAG-powered conversations.
*   **RAG Pipeline:**
    *   Utilizes ChromaDB as a persistent vector store for document embeddings.
    *   Processes and stores documents in session-specific collections.
    *   Retrieves relevant document chunks based on user queries.
*   **LLM-Powered Chat:**
    *   Integrates with the Gemini 1.5 Flash LLM for generating responses.
    *   Maintains **persistent chat memory** for each session, allowing conversations to resume even after refreshing the page or restarting the server.
*   **Session Management:**
    *   Initialize and re-initialize chat sessions.
    *   Delete chat sessions and their associated data from the vector store.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Prime182/AIRA.git
    cd AIRA
    ```
2.  **Create a Python virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Gemini API Key:**
    *   Obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   Create a `.env` file in the root directory of the project (`AIRA/`) and add your API key:
        ```
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
        ```

## Running the Server

To start the Flask backend server:

```bash
python mcp_server.py
```
The server will run on `http://127.0.0.1:5000`.

## User Interface (Streamlit App)

AIRA includes a Streamlit-based web interface located in `ui/streamlit_app.py`. This UI provides a user-friendly way to interact with the AIRA backend, allowing you to:
*   Enter search queries for research material.
*   Select context sources (arXiv, local files, GitHub).
*   View fetched documents.
*   Initiate and manage chat sessions.
*   Engage in RAG-powered conversations.

To run the Streamlit application:

1.  **Ensure the Flask backend server (`mcp_server.py`) is running.**
2.  **Navigate to the `ui` directory:**
    ```bash
    cd ui
    ```
3.  **Run the Streamlit app:**
    ```bash
    streamlit run streamlit_app.py
    ```
    This will typically open the application in your web browser at `http://localhost:8501`.

## API Endpoints

The AIRA backend exposes several REST API endpoints for interaction:

### 1. Get Server Information (MCP Endpoint)
*   **Endpoint:** `/`
*   **Method:** `GET`
*   **Description:** Returns basic information about the server's capabilities, adhering to the MCP server information schema. This endpoint allows other MCP-compatible agents to discover AIRA's functionalities.
*   **Example Response:**
    ```json
    {
      "name": "ResearchAgent",
      "version": "1.0",
      "description": "AI-Powered Research Agent backend.",
      "capabilities": ["fetch_sources", "start_chat", "chat", "delete_session", "search_github_repos", "fetch_repo_readme", "process_github_repo"]
    }
    ```

### 2. Fetch Context Documents
*   **Endpoint:** `/fetch_sources`
*   **Method:** `POST`
*   **Description:** Fetches documents from specified context sources (e.g., `arxiv_api`, `user_local_files`, `github_docs`).
*   **Request Body (JSON):**
    ```json
    {
      "query": "your search query",
      "context_sources": ["arxiv_api"]
    }
    ```
    *   `query`: The search term for sources like arXiv or GitHub.
    *   `context_sources`: A list of sources to fetch from. Valid options: `"arxiv_api"`, `"user_local_files"`, `"github_docs"`.
*   **Example `curl` (PowerShell):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/fetch_sources -Method Post -ContentType "application/json" -Body '{"query": "quantum computing", "context_sources": ["arxiv_api"]}'
    ```
*   **Example Response:** Returns a list of document objects, each with an `id`, `title`, `content`, and `metadata`. You will need these `id`s for `/start_chat`.

### 3. Search GitHub Repositories
*   **Endpoint:** `/search_github_repos`
*   **Method:** `POST`
*   **Description:** Searches GitHub repositories based on a user's query.
*   **Request Body (JSON):**
    ```json
    {
      "query": "your github search term"
    }
    ```
*   **Example `curl` (PowerShell):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/search_github_repos -Method Post -ContentType "application/json" -Body '{"query": "langchain"}'
    ```
*   **Example Response:** Returns a list of repository details (full_name, description, html_url, etc.).

### 4. Fetch GitHub Repository README
*   **Endpoint:** `/fetch_repo_readme`
*   **Method:** `POST`
*   **Description:** Fetches the raw content of a specific GitHub repository's `README.md`.
*   **Request Body (JSON):**
    ```json
    {
      "owner": "repository_owner_username",
      "repo": "repository_name"
    }
    ```
*   **Example `curl` (PowerShell):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/fetch_repo_readme -Method Post -ContentType "application/json" -Body '{"owner": "langchain-ai", "repo": "langchain"}'
    ```
*   **Example Response:** Returns the raw markdown content of the README.

### 5. Process GitHub Repository for Chat
*   **Endpoint:** `/process_github_repo`
*   **Method:** `POST`
*   **Description:** Clones/pulls a specified GitHub repository, parses relevant files (`.md`, `.py`, `.js`, `.ts`), chunks the content, and embeds it into a dedicated ChromaDB collection for RAG. This prepares the repository for LLM-powered conversations.
*   **Request Body (JSON):**
    ```json
    {
      "repo_url": "https://github.com/owner/repo.git",
      "repo_name": "unique_repo_identifier"
    }
    ```
    *   `repo_url`: The full HTTPS clone URL of the GitHub repository.
    *   `repo_name`: A unique name to identify this repository's data in the vector store (e.g., "langchain-repo").
*   **Example `curl` (PowerShell):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/process_github_repo -Method Post -ContentType "application/json" -Body '{"repo_url": "https://github.com/langchain-ai/langchain.git", "repo_name": "langchain-ai-langchain"}'
    ```
*   **Example Response:** `{"status": "success", "message": "Repository 'langchain-ai-langchain' processed and stored."}`

### 6. Start/Re-initialize Chat Session
*   **Endpoint:** `/start_chat`
*   **Method:** `POST`
*   **Description:** Initializes a new chat session by processing selected documents into the vector database, or re-initializes an existing session, loading its chat history.
*   **Request Body (JSON):**
    *   **For a new session:**
        ```json
        {
          "session_id": "your_unique_session_id",
          "document_ids": ["id_from_fetch_sources_1", "id_from_fetch_sources_2"]
        }
        ```
        (Use `document_ids` obtained from `/fetch_sources` or leave empty if processing a GitHub repo via `/process_github_repo` first.)
    *   **For an existing session:**
        ```json
        {
          "session_id": "your_existing_session_id"
        }
        ```
*   **Example `curl` (PowerShell - New Session):**
    ```bash
    # Assuming you have document IDs from a previous /fetch_sources call
    Invoke-RestMethod -Uri http://127.0.0.1:5000/start_chat -Method Post -ContentType "application/json" -Body '{
      "session_id": "my_arxiv_session",
      "document_ids": ["<doc_id_1>", "<doc_id_2>"]
    }'
    ```
*   **Example `curl` (PowerShell - Existing Session):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/start_chat -Method Post -ContentType "application/json" -Body '{"session_id": "my_arxiv_session"}'
    ```
*   **Example Response:** `{"status": "success", "session_id": "...", "message": "...", "chat_history": [...]}`

### 7. Chat with Session
*   **Endpoint:** `/chat`
*   **Method:** `POST`
*   **Description:** Sends a query to an active chat session. The LLM uses RAG with the session's context and maintains conversation history.
*   **Request Body (JSON):**
    ```json
    {
      "session_id": "your_session_id",
      "query": "Your question here"
    }
    ```
*   **Example `curl` (PowerShell):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/chat -Method Post -ContentType "application/json" -Body '{
      "session_id": "my_arxiv_session",
      "query": "What is quantum entanglement?"
    }'
    ```
*   **Example Response:** `{"response": "LLM's answer", "chat_history": [...]}`

### 8. Delete Chat Session
*   **Endpoint:** `/delete_session`
*   **Method:** `POST`
*   **Description:** Deletes a specific chat session and its associated vector store data.
*   **Request Body (JSON):**
    ```json
    {
      "session_id": "session_to_delete_id"
    }
    ```
*   **Example `curl` (PowerShell):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/delete_session -Method Post -ContentType "application/json" -Body '{"session_id": "my_arxiv_session"}'
    ```
*   **Example Response:** `{"status": "success", "message": "Session 'my_arxiv_session' and its data deleted."}`
