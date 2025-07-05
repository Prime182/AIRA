from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ToolInputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any]
    required: List[str]

class Tool(BaseModel):
    name: str
    description: str
    input_schema: ToolInputSchema

class ServerInfo(BaseModel):
    name: str
    description: str
    version: str
    tools: List[Tool]
    resources: List[str] # List of resource URIs

# Define the specific input schema for our research agent tool
class ResearchAgentQueryInput(BaseModel):
    query: str = Field(..., description="The research question to ask.")
    context_sources: List[str] = Field(..., description="A list of context sources to use (e.g., 'arxiv_api', 'github_docs').")

# Create the tool definition
research_agent_tool = Tool(
    name="research_agent_query",
    description="Performs a research query using specified context sources, processes the information, and returns a response from Gemini.",
    input_schema=ToolInputSchema(
        properties=ResearchAgentQueryInput.model_json_schema()["properties"],
        required=["query", "context_sources"]
    )
)

# Define the overall server information
server_info = ServerInfo(
    name="AIRA_MCP_Server",
    description="An AI-Powered Research Agent that uses multiple context sources to answer questions.",
    version="1.0.0",
    tools=[research_agent_tool],
    resources=[] # No resources defined for now
)
