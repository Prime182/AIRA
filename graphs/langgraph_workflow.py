import os
from langsmith import traceable
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from modules.rag_pipeline import query_vector_db
from modules.gemini_llm import get_gemini_response

# Define the state for our graph
class AgentState(TypedDict):
    query: str
    session_id: str
    model_name: str # Added to carry the selected model
    context: List[str]
    response: str

# --- Graph Nodes ---

def retrieve_node(state: AgentState):
    """Retrieves documents from the vector DB."""
    print(f"---Retrieving documents for query: '{state['query']}'---")
    state['context'] = query_vector_db(state['query'], collection_name=state['session_id'])
    return state

def grade_documents_node(state: AgentState):
    """
    Grades the relevance of retrieved documents.
    This is a simplified grader that checks if any documents were returned.
    A more advanced implementation could use an LLM to score relevance.
    """
    print("---Grading retrieved documents---")
    if not state.get('context'):
        print("---No documents found or context is empty.---")
        state['response'] = "No relevant documents found to answer your query."
        return state
    print("---Documents found, proceeding to generation.---")
    return state

def generate_node(state: AgentState):
    """Calls Gemini to generate a response based on the context."""
    model_name = state.get("model_name", "gemini-1.5-flash") # Default to flash
    print(f"---Generating response with {model_name}---")
    # The get_gemini_response function expects context to be a list of strings.
    context_list = [str(item) for item in state.get('context', [])]
    state['response'] = get_gemini_response(state['query'], context_list, model_name=model_name)
    return state

def decide_next_node(state: AgentState):
    """Determines the next step based on whether relevant documents were found."""
    if not state.get('context'):
        return "end"  # End the graph if no context
    else:
        return "generate"  # Proceed to generate a response

# --- Compile Workflow ---

workflow = StateGraph(AgentState)

# Add the nodes
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("grade_documents", grade_documents_node)
workflow.add_node("generate", generate_node)

# Set the entrypoint
workflow.set_entry_point("retrieve")

# Add the edges
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_next_node,
    {
        "generate": "generate",
        "end": END
    }
)
workflow.add_edge("generate", END)

# Compile the graph
app = workflow.compile()

@traceable(name="LangGraph_RAG_Workflow")
def run_graph_workflow(query: str, session_id: str, model_name: str = "gemini-1.5-flash"):
    """
    Runs the LangGraph RAG workflow with a specified model.
    """
    inputs = {"query": query, "session_id": session_id, "model_name": model_name}
    final_state = app.invoke(inputs)
    return final_state.get("response", "No response generated.")
