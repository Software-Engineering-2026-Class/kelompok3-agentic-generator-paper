import os
from jinja2 import Environment, DictLoader
from .models import LangGraphProject

JINJA_TEMPLATES = {
    "linear": """
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

# Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize Model
llm = ChatOpenAI(model="{{ agents[0].model_name or 'gpt-4o-mini' }}")

def {{ nodes[0].name }}_node(state: AgentState):
    sys_msg = SystemMessage(content=\"\"\"{{ agents[0].prompt }}\"\"\")
    messages = [sys_msg] + state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

# Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("{{ nodes[0].name }}", {{ nodes[0].name }}_node)

workflow.add_edge(START, "{{ nodes[0].name }}")
workflow.add_edge("{{ nodes[0].name }}", END)

app = workflow.compile()

if __name__ == "__main__":
    msgs = app.invoke({"messages": [("user", "Hello!")]})
    print(msgs['messages'][-1].content)
""",
    "tool_calling": """
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

# 1. Define Tools
{% for t in tools %}
@tool
def {{ t.var_name }}(query: str) -> str:
    \"\"\"{{ t.description }}\"\"\"
    return f"Execution of {{ t.var_name }} on {query}"
{% endfor %}

tools_list = [{% for t in tools %}{{ t.var_name }}{% if not loop.last %}, {% endif %}{% endfor %}]

# 2. Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Define the main Agent Node
llm = ChatOpenAI(model="{{ agents[0].model_name or 'gpt-4o-mini' }}")
llm_with_tools = llm.bind_tools(tools_list)

def {{ agents[0].var_name }}_node(state: AgentState):
    sys_msg = SystemMessage(content=\"\"\"{{ agents[0].prompt }}\"\"\")
    messages = [sys_msg] + state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 4. Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", {{ agents[0].var_name }}_node)
workflow.add_node("tools", ToolNode(tools_list))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

app = workflow.compile()

if __name__ == "__main__":
    msgs = app.invoke({"messages": [("user", "Please use your tool to answer this.")]})
    for m in msgs['messages']:
        print(f"{m.type}: {m.content}")
""",
    "supervisor": """
from typing import Annotated, Sequence, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import operator

# Define Supervisors Routing State
class AgentState(TypedDict):
    messages: Annotated[Sequence, add_messages]
    next: str

# 1. Worker Nodes
{% for agent in agents %}
def {{ agent.var_name }}_node(state: AgentState):
    llm = ChatOpenAI(model="{{ agent.model_name or 'gpt-4o-mini' }}")
    sys_msg = SystemMessage(content=\"\"\"{{ agent.prompt }}\"\"\")
    messages = [sys_msg] + state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}
{% endfor %}

# 2. Supervisor Node
def supervisor_node(state: AgentState) -> dict:
    llm = ChatOpenAI(model="gpt-4o")
    # Trivial routing logic demonstration
    prompt = "You are a supervisor. Decide who goes next: " + ", ".join([{% for a in agents %}"{{ a.var_name }}"{% if not loop.last %}, {% endif %}{% endfor %}]) + " or FINISH"
    sys_msg = SystemMessage(content=prompt)
    response = llm.invoke([sys_msg] + state['messages'])
    # Very naive parsing for generated code
    route = "FINISH"
    {% for a in agents %}
    if "{{ a.var_name }}" in response.content:
        route = "{{ a.var_name }}"
    {% endfor %}
    return {"next": route}

# 3. Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
{% for agent in agents %}
workflow.add_node("{{ agent.var_name }}", {{ agent.var_name }}_node)
{% endfor %}

workflow.add_edge(START, "supervisor")

{% for agent in agents %}
workflow.add_edge("{{ agent.var_name }}", "supervisor")
{% endfor %}

# Conditional Routing
def route_step(state: AgentState):
    if state["next"] == "FINISH":
        return END
    return state["next"]

workflow.add_conditional_edges(
    "supervisor",
    route_step,
    {
        "FINISH": END,
        {% for agent in agents %}
        "{{ agent.var_name }}": "{{ agent.var_name }}"{% if not loop.last %},{% endif %}
        {% endfor %}
    }
)

app = workflow.compile()

if __name__ == "__main__":
    msgs = app.invoke({"messages": [("user", "Start the task")]})
    print(msgs['messages'][-1].content)
"""
}

def generate_project(project: LangGraphProject, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    
    env = Environment(loader=DictLoader(JINJA_TEMPLATES))
    
    pattern = project.pattern_type
    if pattern not in JINJA_TEMPLATES:
        pattern = "linear"
        
    template = env.get_template(pattern)
    
    agents = project.agents
    if not agents:
        from .models import AgentModel
        agents = [AgentModel(
            id="default-agent",
            var_name="agent",
            role="assistant",
            prompt="You are a helpful assistant.",
            model_name="gpt-4o-mini"
        )]

    output_code = template.render(
        tools=project.tools,
        agents=agents,
        nodes=[n for n in project.nodes if not n.id.endswith("Graph")] or project.nodes,
        edges=project.edges
    )
    
    main_path = os.path.join(output_dir, "main.py")
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(output_code.strip() + "\n")
        
    # Also write a standard requirements.txt
    req_path = os.path.join(output_dir, "requirements.txt")
    with open(req_path, "w", encoding="utf-8") as f:
        f.write("langgraph>=0.0.26\nlangchain-openai>=0.1.1\nlangchain-core\npython-dotenv\n")
        
    return output_dir
