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
    name: str
    agent_ref: Optional[str] = None
    is_start: bool = False
    is_end: bool = False

class InputVariableModel(BaseModel):
    name: str = Field(..., description="Variable name (e.g. 'origin')")
    default_value: str = Field("", description="Default value if found in KG")
    has_default: bool = Field(False, description="True if KG provides a concrete default value")
    alternative_values: List[str] = Field(
        default_factory=list,
        description="Other example values from KG",
    )

class LangGraphProject(BaseModel):
    name: str = "LangGraph Project"
    tools: List[ToolModel] = Field(default_factory=list)
    agents: List[AgentModel] = Field(default_factory=list)
    nodes: List[NodeModel] = Field(default_factory=list)
    edges: List[EdgeModel] = Field(default_factory=list)
    input_variables: List[InputVariableModel] = Field(
        default_factory=list,
        description="Runtime input variables (from agento-ext:KickoffInputBundle)",
    )

    @property
    def pattern_type(self) -> str:
        has_tools = len(self.tools) > 0
        if len(self.agents) > 1:
            return "supervisor"
        elif has_tools:
            return "tool_calling"
        else:
            return "linear"
