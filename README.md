# AIRA: AI-Powered Research Agent

AIRA (AI-Powered Research Agent) is a backend system designed to facilitate research and information retrieval using Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG). It allows users to fetch context from various sources, process it, and engage in intelligent conversations powered by the Gemini LLM, with persistent chat memory.

## Features

*   **Unified Application Launch:** A single `main.py` script to simultaneously launch both the backend server and the Streamlit frontend in separate terminal windows.
*   **Model Context Protocol (MCP) Server:** AIRA functions as a FastAPI-based MCP server, exposing its capabilities (context fetching, chat, GitHub integration) as tools and resources that can be accessed by other MCP-compatible agents or systems.
*   **Modular Architecture:** Clean separation of functionalities into distinct modules (`context_sources`, `modules`, `graphs`, `utils`) for maintainability and scalability.
*   **Dynamic Context Routing:** The `context_router` intelligently dispatches queries to various context sources and aggregates results into a unified format.
*   **Context Fetching:**
    *   **arXiv API Integration:** Fetch and parse research papers directly from arXiv, including PDF content extraction.
    *   **Local File Processing:** Read and process `.pdf` and `.txt` files from a designated local `data/` directory.
    *   **GitHub Repository Integration:**
        *   Search GitHub repositories based on keywords.
        *   Fetch and preview `README.md` content for any specified repository.
        *   **Deep RAG Integration:** Clone, parse, chunk, and embed content from entire GitHub repositories (supporting `.md`, `.py`, `.js`, `.ts`, and many other common code file types) for comprehensive, code-aware RAG conversations.
*   **Retrieval-Augmented Generation (RAG) Pipeline:**
    *   **Persistent Vector Store:** Utilizes ChromaDB for efficient storage and retrieval of document embeddings.
    *   **Document Processing:** Splits documents into optimized chunks using `RecursiveCharacterTextSplitter` and embeds them using `HuggingFaceEmbeddings`.
    *   **Session-Specific Collections:** Creates and manages isolated vector database collections for each chat session, ensuring context relevance.
*   **LLM-Powered Chat with LangGraph:**
    *   **Gemini LLM Integration:** Seamlessly integrates with Google's Gemini 1.5 Flash and Pro models for generating highly relevant and contextual responses.
    *   **LangGraph Workflow:** Employs a sophisticated LangGraph workflow to orchestrate the RAG process, including document retrieval, relevance grading, and response generation.
    *   **Persistent Chat Memory:** Maintains and loads chat history for each session, allowing users to resume conversations across application restarts.
*   **Rich UI Experience (Streamlit):**
    *   Intuitive web interface for selecting context sources, fetching documents, and managing chat sessions.
    *   Displays fetched documents with previews and allows multi-document selection for chat.
    *   Supports dynamic model selection for Q&A (Gemini 1.5 Flash/Pro).
    *   **Enhanced Code Display:** Automatically detects and renders code snippets in chat responses with syntax highlighting.
    *   **Session Management:** Provides clear options to start new chats, load previous sessions, and delete session data.

## Setup and Installation

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

## Running the Application

AIRA is designed to be launched with a single command, which starts both the backend server and the Streamlit frontend in separate terminal windows.

```bash
python main.py
```

This script will:
1.  Start the FastAPI backend server (`mcp_server.py`) on `http://127.0.0.1:5000`.
2.  Launch the Streamlit web interface (`ui/streamlit_app.py`), typically opening in your web browser at `http://localhost:8501`.

You can close the terminal window where `main.py` was run after the application has launched in new windows.

## API Endpoints

The AIRA backend, powered by FastAPI, exposes several REST API endpoints for interaction. These endpoints allow for programmatic access to AIRA's functionalities, making it suitable for integration with other systems or agents.

### 1. Get Server Information (MCP Endpoint)
*   **Endpoint:** `/`
*   **Method:** `GET`
*   **Description:** Returns basic information about the server's capabilities, adhering to the Model Context Protocol (MCP) server information schema. This endpoint allows other MCP-compatible agents to discover AIRA's functionalities and available tools.
*   **Example Response:**
    ```json
    {
      "name": "AIRA_MCP_Server",
      "description": "An AI-Powered Research Agent that uses multiple context sources to answer questions.",
      "version": "1.0.0",
      "tools": [
        {
          "name": "research_agent_query",
          "description": "Performs a research query using specified context sources, processes the information, and returns a response from Gemini.",
          "input_schema": {
            "type": "object",
            "properties": {
              "query": { "title": "Query", "description": "The research question to ask.", "type": "string" },
              "context_sources": { "title": "Context Sources", "description": "A list of context sources to use (e.g., 'arxiv_api', 'github_docs').", "type": "array", "items": { "type": "string" } }
            },
            "required": ["query", "context_sources"]
          }
        }
      ],
      "resources": []
    }
    ```

### 2. Fetch Context Documents
*   **Endpoint:** `/fetch_sources`
*   **Method:** `POST`
*   **Description:** Fetches documents from specified context sources (e.g., `arxiv_api`, `user_local_files`, `github_docs`). The documents are returned without being processed into the vector store at this stage.
*   **Request Body (JSON):**
    ```json
    {
      "query": "your search query",
      "context_sources": ["arxiv_api"]
    }
    ```
    *   `query`: The search term for sources like arXiv or GitHub. Can be empty for `user_local_files`.
    *   `context_sources`: A list of sources to fetch from. Valid options: `"arxiv_api"`, `"user_local_files"`, `"github_docs"`.
*   **Example `curl` (PowerShell):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/fetch_sources -Method Post -ContentType "application/json" -Body '{"query": "quantum computing", "context_sources": ["arxiv_api"]}'
    ```
*   **Example Response:** Returns a list of document objects, each with a unique `id`, `title`, `content`, and `metadata`. These `id`s are used in the `/start_chat` endpoint to select documents for processing.

### 3. Generate Title and Summary for Chat Session
*   **Endpoint:** `/generate_title_and_summary`
*   **Method:** `POST`
*   **Description:** Generates a concise title and a short summary for a new chat session based on the content of selected documents. This helps in organizing and identifying past conversations.
*   **Request Body (JSON):**
    ```json
    {
      "document_ids": ["id_from_fetch_sources_1", "id_from_fetch_sources_2"]
    }
    ```
    *   `document_ids`: A list of document IDs obtained from the `/fetch_sources` endpoint.
*   **Example `curl` (PowerShell):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/generate_title_and_summary -Method Post -ContentType "application/json" -Body '{"document_ids": ["<doc_id_1>"]}'
    ```
*   **Example Response:**
    ```json
    {
      "title": "Concise Chat Title",
      "summary": "A brief summary of the documents and potential chat topic."
    }
    ```

### 4. Start/Re-initialize Chat Session
*   **Endpoint:** `/start_chat`
*   **Method:** `POST`
*   **Description:** Initializes a new chat session by processing selected documents into a dedicated vector database collection, or re-initializes an existing session by loading its chat history.
*   **Request Body (JSON):**
    *   **For a new session:**
        ```json
        {
          "session_id": "your_unique_session_id",
          "document_ids": ["id_from_fetch_sources_1", "id_from_fetch_sources_2"]
        }
        ```
        (Use `document_ids` obtained from `/fetch_sources`. If processing a GitHub repo via `/process_github_repo` first, `document_ids` can be an empty list as the repo is already processed.)
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

### 5. Chat with Session
*   **Endpoint:** `/chat`
*   **Method:** `POST`
*   **Description:** Sends a query to an active chat session. The LangGraph workflow uses RAG with the session's context and the selected LLM model, maintaining conversation history.
*   **Request Body (JSON):**
    ```json
    {
      "session_id": "your_session_id",
      "query": "Your question here",
      "model": "gemini-1.5-flash"
    }
    ```
    *   `session_id`: The ID of the active chat session.
    *   `query`: The user's question or prompt.
    *   `model`: (Optional) The Gemini model to use for the response (e.g., `"gemini-1.5-flash"`, `"gemini-1.5-pro"`). Defaults to `"gemini-1.5-flash"`.
*   **Example `curl` (PowerShell):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/chat -Method Post -ContentType "application/json" -Body '{
      "session_id": "my_arxiv_session",
      "query": "What is quantum entanglement?",
      "model": "gemini-1.5-pro"
    }'
    ```
*   **Example Response:** `{"response": "LLM's answer", "chat_history": [...]}`

### 6. Delete Chat Session
*   **Endpoint:** `/delete_session`
*   **Method:** `POST`
*   **Description:** Deletes a specific chat session and its associated vector store data from ChromaDB, as well as its chat history file.
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

### 7. Search GitHub Repositories
*   **Endpoint:** `/search_github_repos`
*   **Method:** `POST`
*   **Description:** Searches GitHub repositories based on a user-provided query using the GitHub REST API.
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
*   **Example Response:** Returns a list of repository details (e.g., `full_name`, `description`, `html_url`, `stargazers_count`).

### 8. Fetch GitHub Repository README
*   **Endpoint:** `/fetch_repo_readme`
*   **Method:** `POST`
*   **Description:** Fetches the raw `README.md` content for a given GitHub repository.
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
*   **Example Response:** Returns the raw markdown content of the README as a string.

### 9. Process GitHub Repository for Chat
*   **Endpoint:** `/process_github_repo`
*   **Method:** `POST`
*   **Description:** Clones or pulls a specified GitHub repository, parses relevant files (e.g., `.md`, `.py`, `.js`, `.ts`, etc.), chunks the content, and embeds it into a dedicated ChromaDB collection. This prepares the entire repository's codebase for LLM-powered conversations and deep RAG.
*   **Request Body (JSON):**
    ```json
    {
      "repo_url": "https://github.com/owner/repo.git",
      "repo_name": "unique_repo_identifier"
    }
    ```
    *   `repo_url`: The full HTTPS clone URL of the GitHub repository.
    *   `repo_name`: A unique, sanitized name to identify this repository's data in the vector store (e.g., "langchain-ai-langchain").
*   **Example `curl` (PowerShell):**
    ```bash
    Invoke-RestMethod -Uri http://127.0.0.1:5000/process_github_repo -Method Post -ContentType "application/json" -Body '{"repo_url": "https://github.com/langchain-ai/langchain.git", "repo_name": "langchain-ai-langchain"}'
    ```
*   **Example Response:** `{"status": "success", "message": "Repository 'langchain-ai-langchain' processed and stored."}`
