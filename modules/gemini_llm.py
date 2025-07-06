import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=api_key)

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def get_gemini_response(query: str, context: list, chat_history: list = None) -> str:
    """
    Generates a response from the Gemini LLM based on the query, context, and chat history.
    """
    if chat_history is None:
        chat_history = []

    # Prepare the context as a system instruction or initial message
    context_message = ""
    if context:
        context_message = f"""
        You are an AI assistant. Based on the following context, please answer the user's query.
        Provide a concise summary and include citations where appropriate.

        Context:
        {" ".join(map(str, context))}
        """
    else:
        context_message = "You are an AI assistant. I couldn't find any relevant information in the provided context."

    # Gemini's chat history format is a list of dicts with 'role' and 'parts'
    # Convert our simple history to Gemini's format if needed, or ensure it's already in that format.
    # For simplicity, let's assume chat_history passed in is already in the correct format
    # [{"role": "user", "parts": ["content"]}, {"role": "model", "parts": ["content"]}]

    # Start a chat session with the provided history
    # The context_message can be prepended to the first user query or handled as a system instruction
    # For now, let's add it as the first message in the chat history if it's not empty
    
    # If there's no history, or the first message isn't a system/context message, prepend it.
    # This is a simplified way; a more robust solution might use a dedicated system instruction.
    initial_history = []
    if context_message:
        # Add context as a "user" message that the model responds to implicitly
        # Or, if the model supports system instructions, use that.
        # For now, let's just ensure the context is part of the prompt for the current turn.
        # A better way for persistent context might be to embed it with the query.
        pass # We will integrate context directly into the prompt for each turn.

    # The actual chat history for the model
    gemini_chat_history = []
    for msg in chat_history:
        gemini_chat_history.append({"role": msg["role"], "parts": [msg["content"]]})

    # Create the prompt for the current turn, including context
    current_prompt = f"{context_message}\n\nQuery: {query}"

    try:
        # Start a new chat session with the history
        chat = model.start_chat(history=gemini_chat_history)
        response = chat.send_message(current_prompt)
        return response.text
    except Exception as e:
        return f"An error occurred with the Gemini API: {e}"
