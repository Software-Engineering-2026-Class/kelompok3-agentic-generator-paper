"""
Intermediate Representation (IR) Models for LangGraph extraction.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class ToolModel(BaseModel):
    id: str
    var_name: str
    title: str
    description: str

class AgentModel(BaseModel):
    id: str
    var_name: str
    role: str
    prompt: str
    model_name: str = "gpt-4o-mini"
    tools_refs: List[str] = Field(default_factory=list)

class EdgeModel(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None

class NodeModel(BaseModel):
    id: str
    name: str # e.g., 'StartStep', 'WorkflowStep'
    agent_ref: Optional[str] = None
    is_start: bool = False
    is_end: bool = False

class LangGraphProject(BaseModel):
    name: str = "LangGraph Project"
    tools: List[ToolModel] = Field(default_factory=list)
    agents: List[AgentModel] = Field(default_factory=list)
    nodes: List[NodeModel] = Field(default_factory=list)
    edges: List[EdgeModel] = Field(default_factory=list)
    
    @property
    def pattern_type(self) -> str:
        """Heuristic to detect the LangGraph pattern."""
        has_tools = len(self.tools) > 0
        if len(self.agents) > 1:
            return "supervisor" # Pattern 3: Multi-agent / Supervisor
        elif has_tools:
            return "tool_calling" # Pattern 2: Single agent with tools
        else:
            return "linear" # Pattern 1: Simple linear / chat
