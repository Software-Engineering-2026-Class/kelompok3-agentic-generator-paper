import os
from typing import Annotated, TypedDict
from pathlib import Path
from dotenv import load_dotenv
import yaml

_HERE = Path(__file__).parent
load_dotenv(_HERE / ".env", override=True)

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o")


def _load_inputs() -> dict:
    inputs_path = _HERE / "config" / "inputs.yaml"
    if not inputs_path.exists():
        return {}
    with open(inputs_path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not data:
        return {}
    result = {}
    for k, v in data.items():
        if isinstance(v, list) and v:
            result[k] = str(v[0])
        else:
            result[k] = str(v) if v is not None else ""
    return result


def _build_user_message(inputs: dict) -> str:
    if not inputs:
        return "Please use your tool to answer this."
    filled = {k: v for k, v in inputs.items() if v}
    if not filled:
        return "Please use your tool to answer this."
    parts = [f"{k}={v}" for k, v in filled.items()]
    return "Process this request with the following parameters: " + ", ".join(parts)


# 1. Define Tools

@tool
def extract(query: str) -> str:
    """
Tool name: "extract"
Purpose: Extract TripDetails from conversation history. Bound to the agent's LLM.
Schema (Zod, represented informally):
{
  location: string (describe: The location to plan the trip for. Can be a city, state, or country.),
  startDate: string (optional, describe: The start date of the trip. YYYY-MM-DD),
  endDate: string (optional, describe: The end date of the trip. YYYY-MM-DD),
  numberOfGuests: number (describe: The number of guests. Defaults to 2 if unspecified.)
}
Behavior: the tool returns only fields specified by the user; do not make up values. If location is missing, a clarification message should be generated requesting the location.
"""
    return f"Execution of extract on {query}"

@tool
def classify(query: str) -> str:
    """
Tool name: "classify"
Purpose: Classify whether trip details remain relevant to the user's most recent request.
Schema:
{
  isRelevant: boolean (describe: Whether the trip details are still relevant to the user's request.)
}
Notes: When invoked, tool_choice is set to "classify" in the implementation.
"""
    return f"Execution of classify on {query}"

@tool
def list_accommodations(query: str) -> str:
    """
Tool name: "list-accommodations"
Purpose: A tool to list accommodations for the user. Implementation populates an accommodations list (id, name, price, rating, city, image) using a data generator.
Schema: {} (no input schema fields required in the implementation).
Produces: An accommodations list resource used to populate UI.
"""
    return f"Execution of list_accommodations on {query}"

@tool
def list_restaurants(query: str) -> str:
    """
Tool name: "list-restaurants"
Purpose: A tool to list restaurants for the user. Implementation uses trip details to produce a restaurants list.
Schema: {}.
Produces: A restaurants list resource used to populate UI.
"""
    return f"Execution of list_restaurants on {query}"


tools_list = [extract, classify, list_accommodations, list_restaurants]

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatOpenAI(model=LLM_MODEL)
llm_with_tools = llm.bind_tools(tools_list)

def agent_node(state: AgentState):
    sys_msg = SystemMessage(content="""You are a helpful assistant.""")
    messages = [sys_msg] + state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools_list))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

app = workflow.compile()

if __name__ == "__main__":
    inputs = _load_inputs()
    user_msg = _build_user_message(inputs)
    msgs = app.invoke({"messages": [("user", user_msg)]})
    for m in msgs['messages']:
        print(f"{m.type}: {m.content}")
