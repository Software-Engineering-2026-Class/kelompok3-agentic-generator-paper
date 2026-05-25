from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

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

# 2. Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Define the main Agent Node
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools_list)

def agent_node(state: AgentState):
    sys_msg = SystemMessage(content="""You are a helpful assistant.""")
    messages = [sys_msg] + state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 4. Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools_list))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

app = workflow.compile()

if __name__ == "__main__":
    msgs = app.invoke({"messages": [("user", "Please use your tool to answer this.")]})
    for m in msgs['messages']:
        print(f"{m.type}: {m.content}")
