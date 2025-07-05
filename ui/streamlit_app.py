import streamlit as st
import requests
import uuid

st.title("AIRA - AI-Powered Research Agent")

# --- Session State Initialization ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.fetched_docs = []
    st.session_state.selected_docs = []
    st.session_state.past_chats = {}
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
        for chat_id, chat_data in st.session_state.past_chats.items():
            if st.button(f"Chat on: {chat_data['topic']}", key=chat_id):
                st.session_state.session_id = chat_id
                st.session_state.messages = chat_data["messages"]
                st.session_state.app_stage = "chatting"
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
        selected_titles = []
        for doc in st.session_state.fetched_docs:
            if st.checkbox(f"{doc['title']}", key=doc['id']):
                selected_titles.append(doc['id'])
        
        st.session_state.selected_docs = selected_titles

        if st.button("Start Chat with Selected Documents"):
            with st.spinner("Processing documents and starting chat..."):
                api_url = "http://127.0.0.1:5000/start_chat"
                payload = {"session_id": st.session_state.session_id, "document_ids": st.session_state.selected_docs}
                try:
                    response = requests.post(api_url, json=payload)
                    response.raise_for_status()
                    st.session_state.app_stage = "chatting"
                    st.session_state.past_chats[st.session_state.session_id] = {
                        "topic": ", ".join([doc['title'] for doc in st.session_state.fetched_docs if doc['id'] in st.session_state.selected_docs]),
                        "messages": []
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
            st.markdown(message["content"])

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
    
    # Update past chats history
    if st.session_state.session_id in st.session_state.past_chats:
        st.session_state.past_chats[st.session_state.session_id]["messages"] = st.session_state.messages
