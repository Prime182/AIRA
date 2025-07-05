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

def get_gemini_response(query: str, context: list) -> str:
    """
    Generates a response from the Gemini LLM based on the query and context.
    """
    if not context:
        return "I couldn't find any relevant information to answer your question."

    # Create a prompt template
    prompt = f"""
    Based on the following context, please answer the user's query.
    Provide a concise summary and include citations where appropriate.

    Context:
    {" ".join(map(str, context))}

    Query: {query}

    Answer:
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred with the Gemini API: {e}"
