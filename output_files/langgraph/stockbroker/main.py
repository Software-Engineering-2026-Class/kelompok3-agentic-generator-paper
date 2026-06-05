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

LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


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
def unnamed__tool(query: str) -> str:
    """A tool to get the stock price of a company. Invoked with argument { ticker: string }. When called, the agent fetches one-day and thirty-day price collections from https://api.financialdatasets.ai/prices with specified query parameters (interval, interval_multiplier, start_date, end_date, limit). The thirty-day retrieval may follow next_page_url to aggregate pages."""
    return f"Execution of unnamed__tool on {query}"

@tool
def unnamed__tool_1(query: str) -> str:
    """A tool to get the user's portfolio details. Only called when the user explicitly requests portfolio details. Invoked with argument { get_portfolio: true }."""
    return f"Execution of unnamed__tool_1 on {query}"

@tool
def unnamed__tool_2(query: str) -> str:
    """A tool to buy a stock. Invoked with arguments { ticker: string, quantity: number }. When called, the agent requests a price snapshot from https://api.financialdatasets.ai/prices/snapshot and includes the snapshot and quantity in the UI output."""
    return f"Execution of unnamed__tool_2 on {query}"


tools_list = [unnamed__tool, unnamed__tool_1, unnamed__tool_2]

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatOpenAI(model=LLM_MODEL)
llm_with_tools = llm.bind_tools(tools_list)

def agent_node(state: AgentState):
    sys_msg = SystemMessage(content="""http://www.w3id.org/agentic-ai/onto#StockbrokerSystemPrompt""")
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
