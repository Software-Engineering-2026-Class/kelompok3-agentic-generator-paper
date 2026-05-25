from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

# 1. Define Tools

@tool
def capitalize__utilities_capitalize_sentence_capitalize(query: str) -> str:
    """Tool grouping for two capitalization utilities. Implements two conceptual capabilities: (1) capitalizeSentence: capitalizes the first letter of each word in a sentence by splitting on spaces and transforming tokens; (2) capitalize: capitalizes the first letter of a string. Implementation notes: these utilities treat the delimiter as a space character; they operate on Unicode strings in a straightforward per-character manner. They are pure string-processing utilities with no external dependencies in their conceptual model."""
    return f"Execution of capitalize__utilities_capitalize_sentence_capitalize on {query}"

@tool
def format__messages__utility_format_messages(query: str) -> str:
    """Tool that serializes an ordered collection of messages into a formatted string. Conceptual behavior: iterates over messages, determines role via message.getType(), stringifies content if not a string (conceptually using JSON serialization), wraps content in role-based tags with index attribute, and concatenates the blocks with newlines. This tool expects each message to expose a 'getType' semantics and a content payload that is either string or serializable."""
    return f"Execution of format__messages__utility_format_messages on {query}"


tools_list = [capitalize__utilities_capitalize_sentence_capitalize, format__messages__utility_format_messages]

# 2. Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Define the main Agent Node
llm = ChatOpenAI(model="gpt-4o-mini")
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
