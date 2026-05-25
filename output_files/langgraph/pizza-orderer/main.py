from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

# 1. Define Tools

@tool
def unnamed__tool(query: str) -> str:
    """A tool"""
    return f"Execution of unnamed__tool on {query}"

@tool
def unnamed__tool_1(query: str) -> str:
    """A tool"""
    return f"Execution of unnamed__tool_1 on {query}"


tools_list = [unnamed__tool, unnamed__tool_1]

# 2. Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Define the main Agent Node
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools_list)

def agent_node(state: AgentState):
    sys_msg = SystemMessage(content="""http://www.w3id.org/agentic-ai/onto#prompt_agent_system""")
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
