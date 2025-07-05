from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# Define the state for our graph
class AgentState(TypedDict):
    query: str
    context: list
    response: str
    sender: str
    context_sources: list

@tool
def fetch_context_tool(state: AgentState):
    """Fetches context from the specified sources."""
    # In a real implementation, this would call the context_router
    print(f"Fetching context for query: '{state['query']}' from sources: {state['context_sources']}")
    # Dummy context for now
    return {"context": ["Dummy context 1", "Dummy context 2"]}

@tool
def rerank_documents_tool(state: AgentState):
    """Reranks the fetched documents based on relevance."""
    print("Reranking documents...")
    # Dummy reranking
    return {"context": list(reversed(state["context"]))}

@tool
def summarize_context_tool(state: AgentState):
    """Summarizes the context to generate a final response."""
    print("Summarizing context...")
    # In a real implementation, this would call the Gemini LLM
    summary = f"Summary of context for query '{state['query']}': " + " ".join(state['context'])
    return {"response": summary}

# Define the workflow
workflow = StateGraph(AgentState)

# Add the nodes
workflow.add_node("fetch", fetch_context_tool)
workflow.add_node("rerank", rerank_documents_tool)
workflow.add_node("summarize", summarize_context_tool)

# Set the entrypoint
workflow.set_entry_point("fetch")

# Add the edges
workflow.add_edge("fetch", "rerank")
workflow.add_edge("rerank", "summarize")
workflow.add_edge("summarize", END)

# Compile the graph
app = workflow.compile()

# Example of how to run the graph
if __name__ == "__main__":
    inputs = {"query": "What is LangGraph?", "context_sources": ["arxiv_api"]}
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"Output from node '{key}':")
            print("---")
            print(value)
        print("\n---\n")
