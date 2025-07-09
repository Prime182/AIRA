import streamlit as st
import requests
import uuid
import json
import os

st.title("AIRA - AI-Powered Research Assistant")

CHAT_SESSIONS_FILE = "chat_sessions.json"

def load_chat_sessions():
    if os.path.exists(CHAT_SESSIONS_FILE):
        with open(CHAT_SESSIONS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_chat_sessions(sessions):
    with open(CHAT_SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=4)

# --- Session State Initialization ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.fetched_docs = []
    st.session_state.selected_docs = []
    st.session_state.past_chats = load_chat_sessions() # Load existing sessions
    st.session_state.app_stage = "fetching"
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gemini-1.5-pro" # Default value

# --- Sidebar for Chat History and New Chat ---
with st.sidebar:
    st.header("Chat Sessions")
    if st.button("New Chat"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.fetched_docs = []
        st.session_state.selected_docs = []
        st.session_state.app_stage = "fetching"
        st.rerun()

    if st.session_state.past_chats:
        # Create a list of chat IDs to iterate over, as the dictionary might change during iteration
        chat_ids_to_display = list(st.session_state.past_chats.keys())
        for chat_id in chat_ids_to_display:
            chat_data = st.session_state.past_chats[chat_id]
            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                if st.button(f"Chat on: {chat_data['topic']}", key=f"load_{chat_id}"):
                    st.session_state.session_id = chat_id
                    st.session_state.messages = chat_data["messages"]
                    st.session_state.app_stage = "chatting"
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_{chat_id}"):
                    # Call the backend to delete the session data
                    try:
                        delete_url = "http://127.0.0.1:5000/delete_session"
                        payload = {"session_id": chat_id}
                        response = requests.post(delete_url, json=payload)
                        response.raise_for_status()
                        st.toast(f"Session '{st.session_state.past_chats[chat_id]['topic']}' deleted successfully.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error deleting session from backend: {e}")

                    # Remove from frontend state
                    del st.session_state.past_chats[chat_id]
                    save_chat_sessions(st.session_state.past_chats)
                    
                    # If the deleted chat was the active one, reset to a new chat state
                    if st.session_state.session_id == chat_id:
                        st.session_state.session_id = str(uuid.uuid4())
                        st.session_state.messages = []
                        st.session_state.fetched_docs = []
                        st.session_state.selected_docs = []
                        st.session_state.app_stage = "fetching"
                    st.rerun()

    st.header("Settings")
    st.session_state.selected_model = st.selectbox(
    "Select a model for Q&A:",
    ("gemini-1.5-pro", "gemini-1.5-flash","gemini-2.5-pro", "gemini-2.5-flash"),
    index=0 if st.session_state.selected_model == "gemini-1.5-pro" else 1
)


# --- Main App Logic ---

# Stage 1: Fetching Sources
if st.session_state.app_stage == "fetching":
    st.header("1. Find Your Research Material")
    
    query = st.text_input("Enter a search query for arXiv or leave blank to see local files:", 
                          help="For arXiv, use keywords like 'machine learning', 'quantum physics', etc.")
    
    source = st.radio(
        "Select context source:",
        ["user_local_files", "arxiv_api", "github_docs"],
        index=0,
        format_func=lambda x: {
            "user_local_files": "📁 Local Files",
            "arxiv_api": "🔬 arXiv API",
            "github_docs": "🐙 GitHub Repo"
        }[x]
    )
    selected_sources = [source]

    if st.button("Fetch Sources"):
        with st.spinner("Fetching documents..."):
            api_url = "http://127.0.0.1:5000/fetch_sources"
            payload = {"query": query, "context_sources": selected_sources}
            try:
                response = requests.post(api_url, json=payload)
                response.raise_for_status()
                st.session_state.fetched_docs = response.json().get("documents", [])
                if not st.session_state.fetched_docs:
                    st.warning("No documents found. Please try a different query or check your data folder.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the backend: {e}")

    if st.session_state.fetched_docs:
        st.header("2. Select Documents to Analyze")
        selected_ids = []
        for doc in st.session_state.fetched_docs:
            metadata = doc.get('metadata', {})
            source_type = metadata.get('source_type')
            
            # Use filename for local files, otherwise use title
            if source_type == 'user_local_files':
                title = metadata.get('source', 'Unknown Local File')
            else:
                title = doc.get('title', metadata.get('source', 'Unknown Document'))
            
            st.subheader(title)

            # Only show content preview if it's not a local file
            if source_type != 'user_local_files':
                content_preview = doc.get('content', 'No content preview available.')
                if len(content_preview) > 500:
                    content_preview = content_preview[:500] + "..."
                st.markdown(content_preview)

            # Add a checkbox for selection
            if st.checkbox(f"Select this document", key=doc['id']):
                selected_ids.append(doc['id'])
            st.markdown("---") # Add a separator for clarity
        
        st.session_state.selected_docs = selected_ids

        if st.button("Start Chat with Selected Documents"):
            if not st.session_state.selected_docs:
                st.warning("Please select at least one document to start a chat.")
            else:
                # Determine if any selected document is a GitHub repository
                is_github_repo_selected = False
                selected_github_repo_info = None
                
                for doc_id in st.session_state.selected_docs:
                    doc = next((d for d in st.session_state.fetched_docs if d['id'] == doc_id), None)
                    if doc:
                        # Ensure metadata is a dictionary before getting source
                        metadata = doc.get("metadata") or {}
                        source_url = metadata.get("source", "")
                        if source_url and "github.com" in source_url:
                            is_github_repo_selected = True
                            selected_github_repo_info = doc
                            break
                
                if is_github_repo_selected:
                    # Process the GitHub repository fully
                    repo_url = selected_github_repo_info["metadata"]["source"]
                    # Extract repo_name from full_name or source URL
                    full_name = selected_github_repo_info.get("title", "").replace(" (README Preview)", "").split(" by ")[0]
                    
                    repo_name_for_collection = full_name.replace("/", "-").replace(".", "_") # Sanitize for collection name

                    with st.spinner(f"Cloning and processing the full GitHub repository '{full_name}'. This may take a moment..."):
                        process_api_url = "http://127.0.0.1:5000/process_github_repo"
                        process_payload = {"repo_url": repo_url, "repo_name": repo_name_for_collection}
                        try:
                            process_response = requests.post(process_api_url, json=process_payload)
                            process_response.raise_for_status()
                            st.success(f"Repository '{full_name}' processed successfully!")

                            # Generate title and summary for the repo
                            with st.spinner("Generating title and summary for the repository..."):
                                title_api_url = "http://127.0.0.1:5000/generate_title_and_summary"
                                # We pass the initial README doc ID to get some context
                                title_payload = {"document_ids": [selected_github_repo_info['id']]}
                                try:
                                    title_response = requests.post(title_api_url, json=title_payload)
                                    title_response.raise_for_status()
                                    chat_meta = title_response.json()
                                    topic = chat_meta.get("title", f"Chat about {full_name}")
                                    summary = chat_meta.get("summary", "No summary available.")
                                except requests.exceptions.RequestException as e:
                                    st.error(f"Error generating title: {e}")
                                    topic = f"GitHub: {full_name}"
                                    summary = "Could not generate summary for the repository."

                            # Now start the chat session
                            start_chat_api_url = "http://127.0.0.1:5000/start_chat"
                            start_chat_payload = {"session_id": repo_name_for_collection, "document_ids": []}
                            start_chat_response = requests.post(start_chat_api_url, json=start_chat_payload)
                            start_chat_response.raise_for_status()

                            st.session_state.app_stage = "chatting"
                            st.session_state.session_id = repo_name_for_collection
                            st.session_state.past_chats[st.session_state.session_id] = {
                                "topic": topic,
                                "summary": summary,
                                "messages": start_chat_response.json().get("chat_history", [])
                            }
                            st.rerun()

                        except requests.exceptions.RequestException as e:
                            st.error(f"Error processing GitHub repository or starting chat: {e}")
                else:
                    # Proceed with existing logic for non-GitHub documents
                    with st.spinner("Generating title and summary..."):
                        title_api_url = "http://127.0.0.1:5000/generate_title_and_summary"
                        title_payload = {"document_ids": st.session_state.selected_docs}
                        try:
                            title_response = requests.post(title_api_url, json=title_payload)
                            title_response.raise_for_status()
                            chat_meta = title_response.json()
                            topic = chat_meta.get("title", "Chat about selected documents")
                            summary = chat_meta.get("summary", "No summary available.")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error generating title: {e}")
                            topic = ", ".join([doc['title'] for doc in st.session_state.fetched_docs if doc['id'] in st.session_state.selected_docs])
                            summary = "Could not generate summary."

                    with st.spinner("Processing documents and starting chat..."):
                        api_url = "http://127.0.0.1:5000/start_chat"
                        payload = {"session_id": st.session_state.session_id, "document_ids": st.session_state.selected_docs}
                        try:
                            response = requests.post(api_url, json=payload)
                            response.raise_for_status()
                            st.session_state.app_stage = "chatting"
                            st.session_state.past_chats[st.session_state.session_id] = {
                                "topic": topic,
                                "summary": summary,
                                "messages": response.json().get("chat_history", [])
                            }
                            st.rerun()
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error starting chat session: {e}")

# Stage 2: Chatting
elif st.session_state.app_stage == "chatting":
    st.header("Chat about your selected documents")

    # Display summary if it exists
    current_chat = st.session_state.past_chats.get(st.session_state.session_id, {})
    if "summary" in current_chat:
        with st.expander("Chat Summary", expanded=True):
            st.markdown(current_chat["summary"])

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            content = message["content"]
            if message["role"] == "assistant":
                # Parse content for code blocks
                lines = content.split('\n')
                in_code_block = False
                current_code_block = []
                code_language = None
                
                for line in lines:
                    if line.strip().startswith("```"):
                        if in_code_block:
                            # End of code block
                            st.code("\n".join(current_code_block), language=code_language)
                            current_code_block = []
                            code_language = None
                            in_code_block = False
                        else:
                            # Start of code block
                            in_code_block = True
                            # Extract language if specified (e.g., ```python)
                            lang_spec = line.strip()[3:].strip()
                            if lang_spec:
                                code_language = lang_spec
                            else:
                                code_language = "plaintext" # Default if no language specified
                    elif in_code_block:
                        current_code_block.append(line)
                    else:
                        # Regular text outside code block
                        st.markdown(line)
                
                # If a code block was open at the end of the message
                if in_code_block and current_code_block:
                    st.code("\n".join(current_code_block), language=code_language)
            else:
                st.markdown(content)

    if prompt := st.chat_input("Ask a question about the documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Thinking... (Powered by LangGraph)"):
            # The /chat endpoint now routes to the LangGraph workflow on the backend.
            # To display intermediate steps, the backend would need to stream them back.
            api_url = "http://127.0.0.1:5000/chat"
            payload = {
                "session_id": st.session_state.session_id, 
                "query": prompt,
                "model": st.session_state.selected_model
            }
            try:
                response = requests.post(api_url, json=payload)
                response.raise_for_status()
                assistant_response = response.json().get("response", "Sorry, I couldn't get a response.")
            except requests.exceptions.RequestException as e:
                assistant_response = f"Error connecting to the backend: {e}"
            
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            with st.chat_message("assistant"):
                st.markdown(assistant_response)
    
    # Update past chats history and save
    if st.session_state.session_id in st.session_state.past_chats:
        st.session_state.past_chats[st.session_state.session_id]["messages"] = st.session_state.messages
        save_chat_sessions(st.session_state.past_chats) # Save after message update
