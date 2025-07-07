import os
import uuid
import os
import uuid
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from context_router import fetch_all_context
from modules.rag_pipeline import process_and_store_documents, query_vector_db, delete_session_collection, collection_exists
from modules.gemini_llm import get_gemini_response, get_model
from utils.mcp_schema import server_info, ResearchAgentQueryInput
from context_sources.github_docs import search_github_repos, fetch_readme_content, clone_and_read_repo_files
from modules.memory import load_chat_history, save_chat_history
from graphs.langgraph_workflow import run_graph_workflow
from langchain.docstore.document import Document

app = FastAPI()

# In-memory cache for fetched documents
document_cache = {}

# Pydantic Models for Request Bodies
class FetchSourcesRequest(BaseModel):
    query: str = ""
    context_sources: List[str] = []

class StartChatRequest(BaseModel):
    session_id: str
    document_ids: Optional[List[str]] = None

class ChatRequest(BaseModel):
    session_id: str
    query: str
    model: Optional[str] = "gemini-1.5-flash"

class GenerateTitleRequest(BaseModel):
    document_ids: List[str]

class DeleteSessionRequest(BaseModel):
    session_id: str

class SearchGithubRequest(BaseModel):
    query: str

class FetchReadmeRequest(BaseModel):
    owner: str
    repo: str

class ProcessGithubRepoRequest(BaseModel):
    repo_url: str
    repo_name: str

@app.get("/")
def get_server_info():
    """Return the server's capabilities."""
    return server_info.model_dump()

@app.post("/fetch_sources")
def fetch_sources(req: FetchSourcesRequest):
    """Fetches documents from sources and returns them without processing."""
    try:
        docs = fetch_all_context(req.query, req.context_sources)
        
        serializable_docs = []
        for doc in docs:
            doc_id = str(uuid.uuid4())
            # Store the original Document object in the cache
            document_cache[doc_id] = doc
            
            # Create a serializable version for the frontend
            doc_data = {
                "id": doc_id,
                "title": doc.metadata.get("title", doc.metadata.get("source", "Unknown Source")),
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            serializable_docs.append(doc_data)

        return {"documents": serializable_docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_title_and_summary")
def generate_title_and_summary(req: GenerateTitleRequest):
    """Generates a title and summary for a new chat session."""
    try:
        docs_to_summarize = [document_cache[doc_id] for doc_id in req.document_ids if doc_id in document_cache]
        if not docs_to_summarize:
            raise HTTPException(status_code=404, detail="No documents found to summarize.")

        # Combine content for the prompt
        combined_content = "\n\n---\n\n".join([doc.page_content for doc in docs_to_summarize])
        
        # Truncate for safety, though Gemini has a large context window
        if len(combined_content) > 30000:
            combined_content = combined_content[:30000]

        prompt = f"""Based on the following document(s), please generate a concise, descriptive title and a short, one-paragraph summary for a chat session. The title should be no more than 10 words. The summary should be around 50-100 words.

Return the response as a JSON object with two keys: "title" and "summary".

Documents:
{combined_content}
"""
        
        # Use the faster model for this task
        flash_model = get_model("gemini-1.5-flash")
        response = flash_model.generate_content(prompt)
        
        # Clean up the response text to ensure it's valid JSON
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        try:
            # Parse the JSON response from the model
            result = json.loads(cleaned_text)
            return result
        except json.JSONDecodeError:
            # Fallback if the model doesn't return perfect JSON
            return {"title": "Chat about selected documents", "summary": "Could not automatically generate a summary."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start_chat")
def start_chat(req: StartChatRequest):
    """Processes selected documents and initializes a chat session."""
    try:
        if not req.session_id:
            raise HTTPException(status_code=400, detail="Session ID is required.")

        # If the collection already exists, the session is ready.
        if collection_exists(req.session_id):
            chat_history = load_chat_history(req.session_id)
            return {"status": "success", "session_id": req.session_id, "message": "Session initialized.", "chat_history": chat_history}

        # If the collection doesn't exist, we need document IDs to create it.
        if not req.document_ids:
            raise HTTPException(status_code=400, detail="Document IDs are required to start a new session if a collection does not already exist.")

        # Retrieve original Document objects from the cache
        docs_to_process = [document_cache[doc_id] for doc_id in req.document_ids if doc_id in document_cache]
        
        if not docs_to_process:
            raise HTTPException(status_code=400, detail="No valid documents found in cache to process. Please fetch documents first or provide valid document IDs.")

        # Ensure they are actual Document objects before processing
        langchain_docs = [doc for doc in docs_to_process if isinstance(doc, Document)]
        
        if not langchain_docs:
            raise HTTPException(status_code=400, detail="The selected items could not be processed as valid documents.")

        process_and_store_documents(langchain_docs, collection_name=req.session_id)

        return {"status": "success", "session_id": req.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(req: ChatRequest):
    """Handles chat queries for a specific session."""
    try:
        if not req.session_id or not req.query:
            raise HTTPException(status_code=400, detail="Session ID and query are required.")

        chat_history = load_chat_history(req.session_id)
        
        # Pass the selected model to the workflow
        response_text = run_graph_workflow(req.query, req.session_id, req.model)
        
        # Prepare the user message, including the model used for the query
        user_message = {
            "role": "user",
            "content": req.query,
            "metadata": {"model_used": req.model}
        }
        
        chat_history.append(user_message)
        chat_history.append({"role": "assistant", "content": response_text})
        save_chat_history(req.session_id, chat_history)
        
        return {"response": response_text, "chat_history": chat_history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delete_session")
def delete_session(req: DeleteSessionRequest):
    """Deletes a specific chat session and its associated vector store."""
    try:
        if not req.session_id:
            raise HTTPException(status_code=400, detail="Session ID is required.")

        delete_session_collection(req.session_id)
        
        return {"status": "success", "message": f"Session '{req.session_id}' and its data deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search_github_repos")
def search_repos(req: SearchGithubRequest):
    """Searches GitHub repositories based on a query."""
    try:
        if not req.query:
            raise HTTPException(status_code=400, detail="Query parameter is required.")
        
        repos = search_github_repos(req.query)
        return {"repositories": repos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch_repo_readme")
def get_repo_readme(req: FetchReadmeRequest):
    """Fetches the README.md content for a given GitHub repository."""
    try:
        if not req.owner or not req.repo:
            raise HTTPException(status_code=400, detail="Owner and repository name are required.")
        
        readme_content = fetch_readme_content(req.owner, req.repo)
        return {"readme_content": readme_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_github_repo")
def process_github_repo(req: ProcessGithubRepoRequest):
    """Clones, parses, chunks, and embeds a selected GitHub repository."""
    try:
        if not req.repo_url or not req.repo_name:
            raise HTTPException(status_code=400, detail="Repository URL and name are required.")

        clone_dir = os.path.join("data", req.repo_name)
        
        docs_data = clone_and_read_repo_files(req.repo_url, clone_dir)
        
        if not docs_data:
            raise HTTPException(status_code=500, detail="No documents found or processed from the repository.")

        langchain_docs = [Document(page_content=d["content"], metadata={"source": d["source"], "repo_name": req.repo_name}) for d in docs_data]

        process_and_store_documents(langchain_docs, collection_name=req.repo_name)

        return {"status": "success", "message": f"Repository '{req.repo_name}' processed and stored."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
