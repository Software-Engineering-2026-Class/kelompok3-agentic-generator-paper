import rdflib
import re
from rdflib import Graph, URIRef
from .models import LangGraphProject, AgentModel, ToolModel, NodeModel, EdgeModel, InputVariableModel

def to_snake_case(name: str) -> str:
    sStyle = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    sStyle = re.sub(r'[\W]+', '_', sStyle).strip('_')
    return sStyle if sStyle else "node"

def extract_langgraph_project(kg_path: str) -> LangGraphProject:
    g = Graph()
    g.parse(kg_path, format="turtle")

    agento = rdflib.Namespace("http://www.w3id.org/agentic-ai/onto#")
    dct = rdflib.Namespace("http://purl.org/dc/terms/")

    project = LangGraphProject()

    seen_tool_vars = set()
    seen_agent_vars = set()

    def make_unique(base_name: str, seen_set: set) -> str:
        s = to_snake_case(base_name)
        if not s:
            s = "unnamed"
        candidate = s
        counter = 1
        while candidate in seen_set:
            candidate = f"{s}_{counter}"
            counter += 1
        seen_set.add(candidate)
        return candidate

    for tool_uri in g.subjects(rdflib.RDF.type, agento.Tool):
        title = str(g.value(tool_uri, dct.title) or "Unnamed Tool")
        desc = str(g.value(tool_uri, dct.description) or "A tool")
        var_name = make_unique(title, seen_tool_vars)
        project.tools.append(ToolModel(
            id=str(tool_uri),
            var_name=var_name,
            title=title,
            description=desc
        ))

    agent_nodes = list(g.subjects(rdflib.RDF.type, agento.LLMAgent))
    for agent_uri in agent_nodes:
        role = str(g.value(agent_uri, agento.agentRole) or "agent")
        prompt = str(g.value(agent_uri, agento.agentPrompt) or "You are a helpful assistant.")
        agent_title = str(g.value(agent_uri, dct.title) or "Agent")
        var_name = make_unique(agent_title, seen_agent_vars)

        model_name = "gpt-4o-mini"
        for config_uri in g.objects(agent_uri, agento.hasAgentConfig):
            config_key = g.value(config_uri, agento.configKey)
            if config_key and str(config_key) == "model":
                val = g.value(config_uri, agento.configValue)
                if val:
                    model_name = str(val)

        project.agents.append(AgentModel(
            id=str(agent_uri),
            var_name=var_name,
            role=role,
            prompt=prompt,
            model_name=model_name
        ))

    steps = set(g.subjects(rdflib.RDF.type, agento.WorkflowStep)).union(
             g.subjects(rdflib.RDF.type, agento.StartStep))

    for step_uri in steps:
        step_title = str(g.value(step_uri, dct.title) or step_uri.split("#")[-1])
        var_name = to_snake_case(step_title)

        is_start = False
        if (step_uri, rdflib.RDF.type, agento.StartStep) in g:
            is_start = True

        task_uri = g.value(step_uri, agento.hasAssociatedTask)
        agent_ref = None
        if task_uri:
            a_ref = g.value(task_uri, agento.performedByAgent)
            if a_ref:
                agent_ref = str(a_ref)

        project.nodes.append(NodeModel(
            id=str(step_uri),
            name=var_name,
            agent_ref=agent_ref,
            is_start=is_start
        ))

        for next_step_uri in g.objects(step_uri, agento.nextStep):
            project.edges.append(EdgeModel(
                source=str(step_uri),
                target=str(next_step_uri)
            ))

    project.input_variables = _extract_input_variables(g)

    return project


def _extract_input_variables(g: Graph) -> list:
    kickoff_q = """
    PREFIX agento_ext: <http://www.w3id.org/agentic-ai/ext#>
    SELECT ?key ?value ?isDefault
    WHERE {
        ?bundle a agento_ext:KickoffInputBundle ;
                agento_ext:inputKey ?key ;
                agento_ext:inputValue ?value ;
                agento_ext:isDefaultValue ?isDefault .
    }
    """
    rows = list(g.query(kickoff_q))
    if not rows:
        return []

    by_key: dict = {}
    for row in rows:
        key = str(row.key).strip()
        value = str(row.value).strip() if row.value is not None else ""
        is_default_raw = str(row.isDefault).strip().lower() if row.isDefault is not None else "false"
        is_default = is_default_raw in ("true", "1", "yes")

        if key not in by_key:
            by_key[key] = {"default": "", "is_default": False, "alts": []}

        if is_default and not by_key[key]["is_default"]:
            by_key[key]["default"] = value
            by_key[key]["is_default"] = True
        elif value:
            by_key[key]["alts"].append(value)

    return [
        InputVariableModel(
            name=k,
            default_value=v["default"],
            has_default=v["is_default"] and bool(v["default"]),
            alternative_values=v["alts"],
        )
        for k, v in by_key.items()
    ]
