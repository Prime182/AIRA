from flask import Flask, request, jsonify
from pydantic import ValidationError
from context_router import fetch_all_context
from modules.rag_pipeline import process_and_store_documents, query_vector_db, delete_session_collection, collection_exists
from modules.gemini_llm import get_gemini_response
from utils.mcp_schema import server_info, ResearchAgentQueryInput
import uuid

app = Flask(__name__)

# In-memory cache for fetched documents
document_cache = {}

@app.route("/", methods=["GET"])
def get_server_info():
    """Return the server's capabilities."""
    return jsonify(server_info.model_dump())

@app.route("/fetch_sources", methods=["POST"])
def fetch_sources():
    """Fetches documents from sources and returns them without processing."""
    try:
        data = request.get_json()
        query = data.get("query", "")
        sources = data.get("context_sources", [])
        
        # This now returns Document objects with metadata
        docs = fetch_all_context(query, sources)
        
        # Prepare documents for the UI, making them serializable
        serializable_docs = []
        for doc in docs:
            doc_id = str(uuid.uuid4())
            doc_data = {
                "id": doc_id,
                "title": doc.metadata.get("title", doc.metadata.get("source", "Unknown Source")),
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            serializable_docs.append(doc_data)
            document_cache[doc_id] = doc # Cache the full Document object

        return jsonify({"documents": serializable_docs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/start_chat", methods=["POST"])
def start_chat():
    """Processes selected documents and initializes a chat session."""
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        document_ids = data.get("document_ids")

        if not session_id:
            return jsonify({"error": "Session ID is required."}), 400

        # Check if the collection for this session already exists
        if collection_exists(session_id):
            return jsonify({"status": "success", "session_id": session_id, "message": "Session already exists and re-initialized."})

        # If collection does not exist, we need document_ids to create it
        if not document_ids:
            return jsonify({"error": "Document IDs are required to start a new session."}), 400

        # Retrieve the full Document objects from the cache
        docs_to_process = [document_cache[doc_id] for doc_id in document_ids if doc_id in document_cache]
        
        if not docs_to_process:
            return jsonify({"error": "No valid documents found in cache to process. Please fetch documents first or provide valid document IDs."}), 400

        # Process and store these specific documents in a session-specific collection
        process_and_store_documents(docs_to_process, collection_name=session_id)

        return jsonify({"status": "success", "session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Handles chat queries for a specific session."""
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        query = data.get("query")

        if not session_id or not query:
            return jsonify({"error": "Session ID and query are required."}), 400

        # Query the session-specific collection
        relevant_context = query_vector_db(query, collection_name=session_id)
        
        # Get the response from Gemini
        response = get_gemini_response(query, relevant_context)
        
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/delete_session", methods=["POST"])
def delete_session():
    """Deletes a specific chat session and its associated vector store."""
    try:
        data = request.get_json()
        session_id = data.get("session_id")

        if not session_id:
            return jsonify({"error": "Session ID is required."}), 400

        delete_session_collection(session_id)
        
        # Optionally, remove from in-memory cache if you track sessions there
        # For now, we only delete the ChromaDB collection

        return jsonify({"status": "success", "message": f"Session '{session_id}' and its data deleted."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)
