import json
import os

CHAT_SESSIONS_DIR = "data/chat_sessions"

def _get_session_file_path(session_id: str) -> str:
    """Constructs the file path for a given session's chat history."""
    os.makedirs(CHAT_SESSIONS_DIR, exist_ok=True)
    return os.path.join(CHAT_SESSIONS_DIR, f"{session_id}.json")

def load_chat_history(session_id: str) -> list:
    """
    Loads chat history for a given session ID from a JSON file.
    Returns an empty list if the file does not exist or is empty.
    """
    file_path = _get_session_file_path(session_id)
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                if isinstance(history, list):
                    return history
                else:
                    print(f"Warning: Chat history for session {session_id} is not a list. Starting new history.")
                    return []
        except json.JSONDecodeError as e:
            print(f"Error decoding chat history for session {session_id}: {e}. Starting new history.")
            return []
    return []

def save_chat_history(session_id: str, history: list):
    """
    Saves chat history for a given session ID to a JSON file.
    """
    file_path = _get_session_file_path(session_id)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving chat history for session {session_id}: {e}")
