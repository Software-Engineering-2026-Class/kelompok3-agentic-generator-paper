import os
from typing import Annotated, TypedDict
from pathlib import Path
from dotenv import load_dotenv
import yaml

_HERE = Path(__file__).parent
load_dotenv(_HERE / ".env", override=True)

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

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


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatOpenAI(model=LLM_MODEL)

def chat_node(state: AgentState):
    sys_msg = SystemMessage(content="""http://www.w3id.org/agentic-ai/onto#ChatSystemPrompt""")
    messages = [sys_msg] + state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

workflow = StateGraph(AgentState)
workflow.add_node("chat", chat_node)

workflow.add_edge(START, "chat")
workflow.add_edge("chat", END)

app = workflow.compile()

if __name__ == "__main__":
    inputs = _load_inputs()
    user_msg = _build_user_message(inputs)
    msgs = app.invoke({"messages": [("user", user_msg)]})
    print(msgs['messages'][-1].content)
