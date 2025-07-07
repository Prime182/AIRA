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

# Model cache
_models = {}

def get_model(model_name: str = "gemini-1.5-flash"):
    """
    Returns a specific Gemini model instance.
    Caches models to avoid re-initializing them.
    """
    if model_name not in _models:
        # The model name in the library might not have "-latest"
        model_name_for_api = model_name.replace("-latest", "")
        _models[model_name] = genai.GenerativeModel(model_name_for_api)
    return _models[model_name]

def get_gemini_response(query: str, context: list, model_name: str = "gemini-1.5-flash", chat_history: list = None) -> str:
    """
    Generates a response from the Gemini LLM based on the query, context, and specified model.
    """
    context_str = "\n".join(map(str, context))
    
    prompt = f"""Let's answer the following research query step by step.
Query: {query}
Context:
{context_str}

Answer:"""

    try:
        model = get_model(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"---GEMINI API ERROR for model {model_name}: {e}---")
        raise e
