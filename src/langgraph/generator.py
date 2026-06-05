import os
from jinja2 import Environment, DictLoader
from .models import LangGraphProject

JINJA_TEMPLATES = {
    "linear": """
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

LLM_MODEL = os.environ.get("LLM_MODEL", "{{ agents[0].model_name or 'gpt-4o-mini' }}")


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

def {{ nodes[0].name }}_node(state: AgentState):
    sys_msg = SystemMessage(content=\"\"\"{{ agents[0].prompt }}\"\"\")
    messages = [sys_msg] + state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

workflow = StateGraph(AgentState)
workflow.add_node("{{ nodes[0].name }}", {{ nodes[0].name }}_node)

workflow.add_edge(START, "{{ nodes[0].name }}")
workflow.add_edge("{{ nodes[0].name }}", END)

app = workflow.compile()

if __name__ == "__main__":
    inputs = _load_inputs()
    user_msg = _build_user_message(inputs)
    msgs = app.invoke({"messages": [("user", user_msg)]})
    print(msgs['messages'][-1].content)
""",
    "tool_calling": """
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

LLM_MODEL = os.environ.get("LLM_MODEL", "{{ agents[0].model_name or 'gpt-4o-mini' }}")


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
{% for t in tools %}
@tool
def {{ t.var_name }}(query: str) -> str:
    \"\"\"{{ t.description }}\"\"\"
    return f"Execution of {{ t.var_name }} on {query}"
{% endfor %}

tools_list = [{% for t in tools %}{{ t.var_name }}{% if not loop.last %}, {% endif %}{% endfor %}]

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatOpenAI(model=LLM_MODEL)
llm_with_tools = llm.bind_tools(tools_list)

def {{ agents[0].var_name }}_node(state: AgentState):
    sys_msg = SystemMessage(content=\"\"\"{{ agents[0].prompt }}\"\"\")
    messages = [sys_msg] + state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

workflow = StateGraph(AgentState)
workflow.add_node("agent", {{ agents[0].var_name }}_node)
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
""",
    "supervisor": """
import os
from typing import Annotated, Sequence, TypedDict, Literal
from pathlib import Path
from dotenv import load_dotenv
import yaml
import operator

_HERE = Path(__file__).parent
load_dotenv(_HERE / ".env", override=True)

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

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
        return "Start the task"
    filled = {k: v for k, v in inputs.items() if v}
    if not filled:
        return "Start the task"
    parts = [f"{k}={v}" for k, v in filled.items()]
    return "Process this request with the following parameters: " + ", ".join(parts)


class AgentState(TypedDict):
    messages: Annotated[Sequence, add_messages]
    next: str

# 1. Worker Nodes
{% for agent in agents %}
def {{ agent.var_name }}_node(state: AgentState):
    llm = ChatOpenAI(model=os.environ.get("LLM_MODEL", "{{ agent.model_name or 'gpt-4o-mini' }}"))
    sys_msg = SystemMessage(content=\"\"\"{{ agent.prompt }}\"\"\")
    messages = [sys_msg] + state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}
{% endfor %}

# 2. Supervisor Node
def supervisor_node(state: AgentState) -> dict:
    llm = ChatOpenAI(model=os.environ.get("LLM_MODEL", "gpt-4o"))
    prompt = "You are a supervisor. Decide who goes next: " + ", ".join([{% for a in agents %}"{{ a.var_name }}"{% if not loop.last %}, {% endif %}{% endfor %}]) + " or FINISH"
    sys_msg = SystemMessage(content=prompt)
    response = llm.invoke([sys_msg] + state['messages'])
    route = "FINISH"
    {% for a in agents %}
    if "{{ a.var_name }}" in response.content:
        route = "{{ a.var_name }}"
    {% endfor %}
    return {"next": route}

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
{% for agent in agents %}
workflow.add_node("{{ agent.var_name }}", {{ agent.var_name }}_node)
{% endfor %}

workflow.add_edge(START, "supervisor")

{% for agent in agents %}
workflow.add_edge("{{ agent.var_name }}", "supervisor")
{% endfor %}

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
    inputs = _load_inputs()
    user_msg = _build_user_message(inputs)
    msgs = app.invoke({"messages": [("user", user_msg)]})
    print(msgs['messages'][-1].content)
"""
}


def _append_yaml_scalar(lines: list, key: str, value: str) -> None:
    if "\n" in value or len(value) > 100:
        lines.append(f"{key}: |")
        for vline in value.split("\n"):
            lines.append(f"  {vline}")
    else:
        needs_quote = any(c in value for c in ":{},[]&*#?|-><!%@`")
        if needs_quote:
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
        else:
            lines.append(f"{key}: {value}")


def _append_yaml_list_item(lines: list, value: str) -> None:
    if "\n" in value or len(value) > 100:
        lines.append("  - |")
        for vline in value.split("\n"):
            lines.append(f"    {vline}")
    else:
        needs_quote = any(c in value for c in ":{},[]&*#?|-><!%@`")
        if needs_quote:
            escaped = value.replace('"', '\\"')
            lines.append(f'  - "{escaped}"')
        else:
            lines.append(f"  - {value}")


def build_inputs_yaml(project: LangGraphProject) -> str:
    if not project.input_variables:
        return "# No runtime inputs required for this graph.\n"

    lines: list = [
        "# Runtime inputs for the LangGraph app.",
        "# Edit values below before running python main.py.",
        "#",
        "# When a key maps to a list, main.py uses the FIRST item as the",
        "# runtime value.  Reorder or edit the list to choose a different example.",
        "#",
        "# Variables with no concrete value (defaults to empty string) are",
        "# required - you must provide a value before running.",
        "",
    ]

    for var in project.input_variables:
        all_values: list = []
        if var.has_default and var.default_value:
            all_values.append(var.default_value)
        all_values.extend(var.alternative_values)

        if not all_values:
            lines.append(f'{var.name}: ""  # required - provide a value before running')
            continue

        if len(all_values) == 1:
            _append_yaml_scalar(lines, var.name, all_values[0])
        else:
            lines.append(f"{var.name}:")
            for val in all_values:
                _append_yaml_list_item(lines, val)

    lines.append("")
    return "\n".join(lines)


def build_env_example(project: LangGraphProject) -> str:
    lines = [
        "# Environment configuration for the LangGraph app.",
        "# Copy this file to .env and fill in your actual values.",
        "# The .env file is loaded with override=True so it wins over",
        "# any global environment variables (e.g. OPENAI_API_BASE).",
        "",
        "# LLM API Key (required) - get from https://platform.openai.com/api-keys",
        "OPENAI_API_KEY=your_openai_api_key_here",
        "",
        "# Optional: override the OpenAI base URL (e.g. for DeepInfra, Azure, etc.)",
        "# OPENAI_API_BASE=https://api.openai.com/v1",
        "",
        "# Optional: override the default model (default: gpt-4o-mini)",
        "# LLM_MODEL=gpt-4o-mini",
        "",
    ]
    return "\n".join(lines)


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

    config_dir = os.path.join(output_dir, "config")
    os.makedirs(config_dir, exist_ok=True)
    inputs_path = os.path.join(config_dir, "inputs.yaml")
    with open(inputs_path, "w", encoding="utf-8") as f:
        f.write(build_inputs_yaml(project))

    env_example_path = os.path.join(output_dir, ".env.example")
    with open(env_example_path, "w", encoding="utf-8") as f:
        f.write(build_env_example(project))

    req_path = os.path.join(output_dir, "requirements.txt")
    with open(req_path, "w", encoding="utf-8") as f:
        f.write("langgraph>=0.0.26\nlangchain-openai>=0.1.1\nlangchain-core\npython-dotenv\npyyaml>=6.0\n")

    return output_dir
