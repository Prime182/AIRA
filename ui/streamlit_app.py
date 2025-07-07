import streamlit as st
import requests
import uuid
import json
import os

st.title("AIRA - AI-Powered Research Agent")

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
                    del st.session_state.past_chats[chat_id]
                    save_chat_sessions(st.session_state.past_chats) # Save after deletion
                    if st.session_state.session_id == chat_id: # If current chat is deleted, start new one
                        st.session_state.session_id = str(uuid.uuid4())
                        st.session_state.messages = []
                        st.session_state.app_stage = "fetching"
                    st.rerun()

# --- Main App Logic ---

# Stage 1: Fetching Sources
if st.session_state.app_stage == "fetching":
    st.header("1. Find Your Research Material")
    
    query = st.text_input("Enter a search query for arXiv or leave blank to see local files:", 
                          help="For arXiv, use keywords like 'machine learning', 'quantum physics', etc.")
    
    selected_sources = st.multiselect(
        "Select context sources:",
        ["arxiv_api", "user_local_files", "github_docs"],
        default=["arxiv_api"]
    )

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
            # Display the title (repo name and owner for GitHub docs)
            st.subheader(doc.get('title', doc.get('source', 'Unknown Document')))
            st.markdown(doc.get('content', 'No content preview available.'))
            # Add a checkbox for selection
            if st.checkbox(f"Select this document", key=doc['id']):
                selected_ids.append(doc['id'])
            st.markdown("---") # Add a separator for clarity
        
        st.session_state.selected_docs = selected_ids

        if st.button("Start Chat with Selected Documents"):
            if not st.session_state.selected_docs:
                st.warning("Please select at least one document to start a chat.")
            else:
                st.write("--- Debugging Start Chat ---")
                st.info("--- Debugging Start Chat ---")
                st.info(f"Selected Document IDs: {st.session_state.selected_docs}")

                # Determine if any selected document is a GitHub repository
                is_github_repo_selected = False
                selected_github_repo_info = None
                
                for doc_id in st.session_state.selected_docs:
                    doc = next((d for d in st.session_state.fetched_docs if d['id'] == doc_id), None)
                    st.info(f"Checking doc_id: {doc_id}")
                    st.info(f"Retrieved doc: {doc}")
                    if doc:
                        source_url = doc.get("metadata", {}).get("source", "") # Corrected path to source URL
                        st.info(f"Doc source: {source_url}")
                        if "github.com" in source_url:
                            is_github_repo_selected = True
                            # Assuming only one GitHub repo will be processed at a time for full RAG
                            # If multiple are selected, we'll take the first one.
                            selected_github_repo_info = doc
                            break 
                
                st.info(f"Is GitHub repo selected: {is_github_repo_selected}")
                st.info(f"Selected GitHub repo info: {selected_github_repo_info}")
                st.info(f"Current app stage: {st.session_state.app_stage}")
                st.info(f"Session ID: {st.session_state.session_id}")

                if is_github_repo_selected:
                    # Process the GitHub repository fully
                    repo_url = selected_github_repo_info["metadata"]["source"] # Corrected path to source URL
                    # Extract repo_name from full_name or source URL
                    full_name = selected_github_repo_info.get("title", "").split(" by ")[0] # "owner/repo_name"
                    if not full_name or " by " not in selected_github_repo_info.get("title", ""):
                        # Fallback if title format is unexpected, try to parse from URL
                        parts = repo_url.split('/')
                        if len(parts) >= 5:
                            full_name = f"{parts[3]}/{parts[4]}" # owner/repo
                        else:
                            full_name = selected_github_repo_info["id"] # Use ID as fallback name
                    
                    repo_name_for_collection = full_name.replace("/", "-").replace(".", "_") # Sanitize for collection name

                    with st.spinner(f"Processing GitHub repository '{full_name}' and starting chat..."):
                        process_api_url = "http://127.0.0.1:5000/process_github_repo"
                        process_payload = {"repo_url": repo_url, "repo_name": repo_name_for_collection}
                        try:
                            process_response = requests.post(process_api_url, json=process_payload)
                            process_response.raise_for_status()
                            st.success(f"Repository '{full_name}' processed successfully!")

                            # Now start the chat session using the processed repo as context
                            start_chat_api_url = "http://127.0.0.1:5000/start_chat"
                            start_chat_payload = {"session_id": repo_name_for_collection} # Use repo_name as session_id
                            start_chat_response = requests.post(start_chat_api_url, json=start_chat_payload)
                            start_chat_response.raise_for_status()

                            st.session_state.app_stage = "chatting"
                            st.session_state.session_id = repo_name_for_collection # Set current session ID
                            st.session_state.past_chats[st.session_state.session_id] = {
                                "topic": f"GitHub: {full_name}",
                                "messages": start_chat_response.json().get("chat_history", []) # Load existing history if any
                            }
                            st.rerun()

                        except requests.exceptions.RequestException as e:
                            st.error(f"Error processing GitHub repository or starting chat: {e}")
                else:
                    # Proceed with existing logic for non-GitHub documents
                    with st.spinner("Processing documents and starting chat..."):
                        api_url = "http://127.0.0.1:5000/start_chat"
                        payload = {"session_id": st.session_state.session_id, "document_ids": st.session_state.selected_docs}
                        try:
                            response = requests.post(api_url, json=payload)
                            response.raise_for_status()
                            st.session_state.app_stage = "chatting"
                            st.session_state.past_chats[st.session_state.session_id] = {
                                "topic": ", ".join([doc['title'] for doc in st.session_state.fetched_docs if doc['id'] in st.session_state.selected_docs]),
                                "messages": response.json().get("chat_history", []) # Load existing history if any
                            }
                            st.rerun()
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error starting chat session: {e}")

# Stage 2: Chatting
elif st.session_state.app_stage == "chatting":
    st.header("Chat about your selected documents")

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

        with st.spinner("Thinking..."):
            api_url = "http://127.0.0.1:5000/chat"
            payload = {"session_id": st.session_state.session_id, "query": prompt}
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
