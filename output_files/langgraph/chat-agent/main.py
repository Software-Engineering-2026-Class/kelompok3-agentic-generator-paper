from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

# Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize Model
llm = ChatOpenAI(model="gpt-4o-mini")

def chat_node(state: AgentState):
    sys_msg = SystemMessage(content="""http://www.w3id.org/agentic-ai/onto#ChatSystemPrompt""")
    messages = [sys_msg] + state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

# Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("chat", chat_node)

workflow.add_edge(START, "chat")
workflow.add_edge("chat", END)

app = workflow.compile()

if __name__ == "__main__":
    msgs = app.invoke({"messages": [("user", "Hello!")]})
    print(msgs['messages'][-1].content)
