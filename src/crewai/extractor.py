"""
Layer 1 – SPARQL-based Data Extraction

Loads a CrewAI KG (.ttl) file via rdflib, runs SPARQL queries aligned
to the agentO ontology, and populates Pydantic IR models (Layer 2).

Extraction strategy:
  1. Team / Crew metadata + process type
  2. LanguageModel individuals
  3. Tool individuals (excluding LLMAgent)
  4. Agent individuals — canonical pattern:
       role      → :agentRole literal
       goal      → :hasAgentGoal → Goal → dcterms:description
       backstory → :agentPrompt → Prompt → :promptContext
       allow_delegation / verbose → separate Config per key
  5. Task individuals (with prompt/config fallback for description/expected_output)
  6. Workflow ordering (WorkflowStep chain)
  7. Resource dependency → task context resolution
  8. Template variable extraction from prompt placeholders
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from rdflib import Graph

from .models import (
    AgentModel,
    ConfigModel,
    CrewProject,
    InputVariableModel,
    LanguageModelModel,
    ProcessType,
    TaskModel,
    ToolConfigModel,
    ToolModel,
    WorkflowStepModel,
)


# ─────────────────────── Helpers ───────────────────────

def _s(val: Any) -> str:
    """Convert rdflib term to stripped str."""
    return str(val).strip() if val else ""


def _safe_var(iri: str) -> str:
    """
    IRI fragment → valid Python snake_case identifier.

    e.g. "http://…/onto#SeniorEngineerAgent" → "senior_engineer_agent"
    """
    if not iri:
        return "unnamed"
    name = iri.split("/")[-1].split("#")[-1]
    # Insert _ before uppercase runs: "SeniorEngineer" → "Senior_Engineer"
    name = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    name = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", name)
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    if not name:
        return "unnamed"
    if name[0].isdigit():
        name = f"_{name}"
    return name


def _camel(s: str) -> str:
    """snake_case → CamelCase: 'game_builder_crew' → 'GameBuilderCrew'."""
    return "".join(w.capitalize() for w in s.split("_"))


def _extract_placeholders(text: str) -> List[str]:
    """Extract {placeholder} variable names from a string."""
    return list(dict.fromkeys(re.findall(r"\{(\w+)\}", text)))


def load_graph(file_path: str) -> Graph:
    """Parse a Turtle (.ttl) file into an rdflib Graph."""
    g = Graph()
    g.parse(file_path, format="turtle")
    return g


# ─────────────────────── SPARQL Queries ───────────────────────

PREFIXES = """\
PREFIX : <http://www.w3id.org/agentic-ai/onto#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd:     <http://www.w3.org/2001/XMLSchema#>
PREFIX beam:    <http://w3id.org/beam/core#>
"""

# ── Team ──

TEAM_QUERY = PREFIXES + """
SELECT ?team ?label ?desc
WHERE {
    ?team a :Team .
    OPTIONAL { ?team rdfs:label ?label }
    OPTIONAL { ?team dcterms:description ?desc }
}
"""

TEAM_PROCESS_QUERY = PREFIXES + """
SELECT ?configValue
WHERE {
    ?team a :Team ;
          :hasSystemConfig ?cfg .
    ?cfg :configKey "process" ;
         :configValue ?configValue .
}
"""

# Fallback: detect process type from WorkflowPattern label/desc or Team desc
WORKFLOW_PATTERN_TEXT_QUERY = PREFIXES + """
SELECT ?label ?desc ?comment ?title
WHERE {
    ?wp a :WorkflowPattern .
    OPTIONAL { ?wp rdfs:label ?label }
    OPTIONAL { ?wp dcterms:description ?desc }
    OPTIONAL { ?wp rdfs:comment ?comment }
    OPTIONAL { ?wp dcterms:title ?title }
}
"""

TEAM_DESC_QUERY = PREFIXES + """
SELECT ?desc ?comment
WHERE {
    ?team a :Team .
    OPTIONAL { ?team dcterms:description ?desc }
    OPTIONAL { ?team rdfs:comment ?comment }
}
"""

# ── Language Models ──

LLM_QUERY = PREFIXES + """
SELECT DISTINCT ?lm ?label ?desc
WHERE {
    ?lm a :LanguageModel .
    OPTIONAL { ?lm rdfs:label ?label }
    OPTIONAL { ?lm dcterms:description ?desc }
}
"""

# ── Tools (exclude LLMAgent which is subclass of Tool) ──

TOOLS_QUERY = PREFIXES + """
SELECT DISTINCT ?tool ?label ?desc ?comment
WHERE {
    ?tool a :Tool .
    FILTER NOT EXISTS { ?tool a :LLMAgent }
    OPTIONAL { ?tool rdfs:label ?label }
    OPTIONAL { ?tool dcterms:description ?desc }
    OPTIONAL { ?tool rdfs:comment ?comment }
}
"""

TOOL_CONFIGS_QUERY = PREFIXES + """
SELECT ?tool ?key ?value
WHERE {
    ?tool a :Tool ;
          :hasToolConfig ?cfg .
    ?cfg :configKey ?key ;
         :configValue ?value .
    FILTER NOT EXISTS { ?tool a :LLMAgent }
}
"""

# ── Agents (canonical pattern — single consolidated query) ──
# Extracts all single-valued agent properties in one pass:
#   role, goal, backstory, allow_delegation, verbose
# Multi-valued relations (tools, LLM) remain as separate queries.

AGENTS_QUERY = PREFIXES + """
SELECT DISTINCT ?agent ?agentID ?role ?label ?goalDesc ?backstory
                ?delegation ?verbose
WHERE {
    ?agent a :LLMAgent .
    OPTIONAL { ?agent :agentID ?agentID }
    OPTIONAL { ?agent :agentRole ?role }
    OPTIONAL { ?agent rdfs:label ?label }
    OPTIONAL {
        ?agent :hasAgentGoal ?goal .
        ?goal dcterms:description ?goalDesc .
    }
    OPTIONAL {
        ?agent :agentPrompt ?prompt .
        ?prompt :promptContext ?backstory .
    }
    OPTIONAL {
        ?agent :hasAgentConfig ?cfgD .
        ?cfgD :configKey "allow_delegation" ;
              :configValue ?delegation .
    }
    OPTIONAL {
        ?agent :hasAgentConfig ?cfgV .
        ?cfgV :configKey "verbose" ;
              :configValue ?verbose .
    }
}
"""

AGENT_TOOLS_QUERY = PREFIXES + """
SELECT DISTINCT ?agent ?tool
WHERE {
    ?agent a :LLMAgent ;
           :agentToolUsage ?tool .
    ?tool a :Tool .
    FILTER NOT EXISTS { ?tool a :LLMAgent }
}
"""

AGENT_LLM_QUERY = PREFIXES + """
SELECT DISTINCT ?agent ?lm
WHERE {
    ?agent a :LLMAgent ;
           :useLanguageModel ?lm .
}
"""



# ── Tasks ──

TASKS_QUERY = PREFIXES + """
SELECT DISTINCT ?task ?label ?desc ?agent
WHERE {
    ?task a :Task .
    OPTIONAL { ?task rdfs:label ?label }
    OPTIONAL { ?task dcterms:description ?desc }
    OPTIONAL { ?task :performedByAgent ?agent }
}
"""

TASK_PROMPT_QUERY = PREFIXES + """
SELECT ?task ?instruction ?outputIndicator
WHERE {
    ?task a :Task .
    {
        { ?task :taskPrompt ?prompt }
        UNION
        { ?task :hasPrompt ?prompt }
    }
    ?prompt a :Prompt .
    OPTIONAL { ?prompt :promptInstruction ?instruction }
    OPTIONAL { ?prompt :promptOutputIndicator ?outputIndicator }
}
"""

TASK_EXPECTED_CONFIG_QUERY = PREFIXES + """
SELECT ?task ?value
WHERE {
    ?task a :Task ;
          :hasAgentConfig ?cfg .
    ?cfg :configKey "expected_output" ;
         :configValue ?value .
}
"""

TASK_DESCRIPTION_CONFIG_QUERY = PREFIXES + """
SELECT ?task ?value
WHERE {
    ?task a :Task ;
          :hasAgentConfig ?cfg .
    ?cfg :configKey "description" ;
         :configValue ?value .
}
"""

# ── Task Context (resource dependencies) ──

TASK_PRODUCES_QUERY = PREFIXES + """
SELECT ?task ?resource
WHERE {
    ?task a :Task ;
          :producedResource ?resource .
}
"""

TASK_REQUIRES_QUERY = PREFIXES + """
SELECT ?task ?resource
WHERE {
    ?task a :Task ;
          :requiresResource ?resource .
}
"""

# ── Workflow ──

WORKFLOW_QUERY = PREFIXES + """
SELECT ?step ?stepOrder ?task ?stepType
WHERE {
    ?step :hasAssociatedTask ?task .
    ?step a ?stepType .
    VALUES ?stepType { :WorkflowStep :StartStep :EndStep }
    OPTIONAL { ?step :stepOrder ?stepOrder }
}
ORDER BY ?stepOrder
"""

# ── Input Variables (from prompt input data) ──

PROMPT_INPUT_DATA_QUERY = PREFIXES + """
SELECT DISTINCT ?inputData
WHERE {
    ?prompt a :Prompt ;
            :promptInputData ?inputData .
}
"""

# ── Default inputs (from :Context / beam:Resource) — LEGACY fallback ──

DEFAULT_INPUTS_QUERY = PREFIXES + """
SELECT ?resource ?desc
WHERE {
    {
        ?resource a beam:Resource .
        ?resource dcterms:description ?desc .
        FILTER(CONTAINS(LCASE(STR(?desc)), "input"))
    }
    UNION
    {
        ?resource a :Context .
        ?resource dcterms:description ?desc .
        FILTER(CONTAINS(LCASE(STR(?desc)), "input"))
    }
}
"""

# ── Uniform inputs (agento-ext:KickoffInputBundle) — PRIMARY ──

KICKOFF_INPUTS_QUERY = PREFIXES + """
PREFIX agento_ext: <http://www.w3id.org/agentic-ai/ext#>
SELECT ?key ?value ?isDefault
WHERE {
    ?bundle a agento_ext:KickoffInputBundle ;
            agento_ext:inputKey ?key ;
            agento_ext:inputValue ?value ;
            agento_ext:isDefaultValue ?isDefault .
}
"""

# ── Environment config (API keys) ──

ENV_CONFIG_QUERY = PREFIXES + """
SELECT ?key ?value
WHERE {
    ?cfg a :Config ;
         :configKey ?key ;
         :configValue ?value .
    FILTER(CONTAINS(LCASE(?key), "api_key") || CONTAINS(LCASE(?key), "env"))
}
"""


# ─────────────────────── Extraction functions ───────────────────────

def _infer_process_from_text(text: str) -> Optional[ProcessType]:
    """
    Infer process type from free-text label/description/comment.

    Checks for 'hierarchical' first (rarer, more specific),
    then 'sequential'.  Returns None if neither keyword found.
    """
    if not text:
        return None
    lower = text.lower()
    if "hierarchical" in lower:
        return ProcessType.HIERARCHICAL
    if "sequential" in lower:
        return ProcessType.SEQUENTIAL
    return None


def _extract_team(g: Graph) -> Tuple[str, str, ProcessType]:
    """Extract team name, description, and process type."""
    crew_name = "MyCrew"
    description = ""
    process = ProcessType.SEQUENTIAL

    results = list(g.query(TEAM_QUERY))
    if results:
        row = results[0]
        label = _s(row.label)
        if label:
            # Use label as crew class name, cleaned to CamelCase
            crew_name = re.sub(r"[^a-zA-Z0-9]", "", label)
            if not crew_name:
                crew_name = "MyCrew"
        description = _s(row.desc)

    # ── Strategy 1: explicit configKey "process" (most authoritative) ──
    process_results = list(g.query(TEAM_PROCESS_QUERY))
    detected = False
    for row in process_results:
        val = _s(row.configValue).lower()
        if "hierarchical" in val:
            process = ProcessType.HIERARCHICAL
            detected = True
        elif "sequential" in val:
            process = ProcessType.SEQUENTIAL
            detected = True

    # ── Strategy 2: WorkflowPattern labels/descriptions (common fallback) ──
    if not detected:
        for row in g.query(WORKFLOW_PATTERN_TEXT_QUERY):
            for field_val in [_s(row.label), _s(row.desc), _s(row.comment), _s(row.title)]:
                inferred = _infer_process_from_text(field_val)
                if inferred is not None:
                    process = inferred
                    detected = True
                    # Hierarchical is rarer and more specific — if found, stop
                    if inferred == ProcessType.HIERARCHICAL:
                        break
            if detected and process == ProcessType.HIERARCHICAL:
                break

    # ── Strategy 3: Team description/comment text ──
    if not detected:
        for row in g.query(TEAM_DESC_QUERY):
            for field_val in [_s(row.desc), _s(row.comment)]:
                inferred = _infer_process_from_text(field_val)
                if inferred is not None:
                    process = inferred
                    detected = True
                    break
            if detected:
                break

    return crew_name, description, process


def _extract_language_models(g: Graph) -> Dict[str, LanguageModelModel]:
    """Extract LanguageModel individuals keyed by IRI."""
    models: Dict[str, LanguageModelModel] = {}
    for row in g.query(LLM_QUERY):
        iri = _s(row.lm)
        label = _s(row.label)
        desc = _s(row.desc)

        # Infer provider and model_name from label/description
        provider = ""
        model_name = ""
        text = f"{label} {desc}".lower()
        if "ollama" in text:
            provider = "ollama"
            # Try to extract model name like "llama3.1"
            m = re.search(r"ollama\S*\s*[\(\"']?([a-z0-9._-]+)", text)
            if m:
                model_name = m.group(1)
        elif "openai" in text or "gpt" in text:
            provider = "openai"
            m = re.search(r"(gpt-[a-z0-9._-]+)", text)
            if m:
                model_name = m.group(1)

        models[iri] = LanguageModelModel(
            iri=iri,
            name=label,
            description=desc,
            provider=provider,
            model_name=model_name,
        )
    return models


def _extract_tools(g: Graph) -> Dict[str, ToolModel]:
    """Extract standalone Tool individuals (excluding LLMAgent)."""
    tools: Dict[str, ToolModel] = {}

    for row in g.query(TOOLS_QUERY):
        iri = _s(row.tool)
        if iri in tools:
            continue
        label = _s(row.label)
        desc = _s(row.desc) or _s(row.comment) or ""

        # Infer class name from label
        class_name = label if label else _safe_var(iri)
        # Clean class name: remove spaces, keep CamelCase
        class_name_clean = re.sub(r"[^a-zA-Z0-9]", "", class_name)

        tools[iri] = ToolModel(
            iri=iri,
            var_name=_safe_var(iri),
            label=label,
            class_name=class_name_clean,
            description=desc.strip(),
            configs=[],
            capabilities=[],
        )

    # Tool configs
    for row in g.query(TOOL_CONFIGS_QUERY):
        iri = _s(row.tool)
        if iri in tools:
            tools[iri].configs.append(
                ToolConfigModel(key=_s(row.key), value=_s(row.value))
            )

    return tools


def _extract_agents(
    g: Graph,
    tools_map: Dict[str, ToolModel],
    lm_map: Dict[str, LanguageModelModel],
) -> Dict[str, AgentModel]:
    """Extract LLMAgent individuals from canonical KG pattern.

    Single consolidated SPARQL query extracts all scalar properties:
      role      → :agentRole literal
      goal      → :hasAgentGoal → Goal → dcterms:description
      backstory → :agentPrompt → Prompt → :promptContext
      delegation/verbose → separate Config individuals per key

    Multi-valued relations (tools, LLM) use separate queries.
    """
    agents: Dict[str, AgentModel] = {}

    for row in g.query(AGENTS_QUERY):
        iri = _s(row.agent)
        if iri in agents:
            continue
        agent_id = _s(row.agentID)
        label = _s(row.label)
        role = _s(row.role)

        var_name = agent_id or label or _safe_var(iri)
        var_name = _safe_var(var_name) if not re.match(r'^[a-z_][a-z0-9_]*$', var_name) else var_name

        # Parse allow_delegation
        deleg_val = _s(row.delegation).strip().lower()
        allow_delegation = None
        if deleg_val:
            allow_delegation = deleg_val in ("true", "1", "yes")

        # Parse verbose
        verbose_val = _s(row.verbose).strip().lower()
        verbose = None
        if verbose_val:
            verbose = verbose_val not in ("false", "0", "no", "none")

        agents[iri] = AgentModel(
            iri=iri,
            var_name=var_name,
            agent_id=agent_id,
            role=role,
            goal=_s(row.goalDesc),
            backstory=_s(row.backstory),
            tool_var_names=[],
            llm=None,
            allow_delegation=allow_delegation,
            verbose=verbose,
        )

    # Agent → Tool links (multi-valued, separate query)
    for row in g.query(AGENT_TOOLS_QUERY):
        iri = _s(row.agent)
        tool_iri = _s(row.tool)
        if iri in agents and tool_iri in tools_map:
            tool_var = tools_map[tool_iri].var_name
            if tool_var not in agents[iri].tool_var_names:
                agents[iri].tool_var_names.append(tool_var)

    # Agent → LanguageModel (multi-valued, separate query)
    for row in g.query(AGENT_LLM_QUERY):
        iri = _s(row.agent)
        lm_iri = _s(row.lm)
        if iri in agents and lm_iri in lm_map:
            agents[iri].llm = lm_map[lm_iri]

    # Final defaults
    for agent in agents.values():
        if not agent.role:
            agent.role = "LLM Agent"
        if not agent.goal:
            agent.goal = agent.role
        if not agent.backstory:
            agent.backstory = f"You are a {agent.role}."

    return agents


def _extract_tasks(g: Graph, agents_map: Dict[str, AgentModel]) -> Dict[str, TaskModel]:
    """Extract Task individuals with full property resolution."""
    tasks: Dict[str, TaskModel] = {}

    # Reverse lookup: agent IRI → var_name
    agent_iri_to_var: Dict[str, str] = {a.iri: a.var_name for a in agents_map.values()}

    # Primary task properties
    for row in g.query(TASKS_QUERY):
        iri = _s(row.task)
        if iri in tasks:
            continue

        label = _s(row.label)
        desc = _s(row.desc)
        agent_iri = _s(row.agent)

        var_name = label or _safe_var(iri)
        var_name = _safe_var(var_name) if not re.match(r'^[a-z_][a-z0-9_]*$', var_name) else var_name

        tasks[iri] = TaskModel(
            iri=iri,
            var_name=var_name,
            description=desc,
            expected_output="",
            agent_var_name=agent_iri_to_var.get(agent_iri, ""),
            context_task_var_names=[],
        )

    # Task description from Config (override if richer)
    for row in g.query(TASK_DESCRIPTION_CONFIG_QUERY):
        iri = _s(row.task)
        val = _s(row.value)
        if iri in tasks:
            # Use config description if it's longer (more detailed)
            if len(val) > len(tasks[iri].description):
                tasks[iri].description = val

    # Prompt data
    for row in g.query(TASK_PROMPT_QUERY):
        iri = _s(row.task)
        if iri not in tasks:
            continue
        instr = _s(row.instruction)
        output = _s(row.outputIndicator)
        if output and not tasks[iri].expected_output:
            tasks[iri].expected_output = output
        if instr and not tasks[iri].description:
            tasks[iri].description = instr

    # Expected output from Config
    for row in g.query(TASK_EXPECTED_CONFIG_QUERY):
        iri = _s(row.task)
        val = _s(row.value)
        if iri in tasks and not tasks[iri].expected_output:
            tasks[iri].expected_output = val

    # Final defaults
    for task in tasks.values():
        if not task.description:
            task.description = task.var_name.replace("_", " ").title()
        if not task.expected_output:
            task.expected_output = f"Completed: {task.var_name}"

    return tasks


def _resolve_task_context(g: Graph, tasks_map: Dict[str, TaskModel]) -> None:
    """
    Resolve task context dependencies via producedResource/requiresResource chains.

    If Task B requiresResource R, and Task A producedResource R,
    then Task B's context includes Task A.
    """
    # Build resource → producing task map
    resource_to_producer: Dict[str, str] = {}
    for row in g.query(TASK_PRODUCES_QUERY):
        task_iri = _s(row.task)
        res_iri = _s(row.resource)
        if task_iri in tasks_map:
            resource_to_producer[res_iri] = tasks_map[task_iri].var_name

    # For each task's required resources, find the producing task
    for row in g.query(TASK_REQUIRES_QUERY):
        task_iri = _s(row.task)
        res_iri = _s(row.resource)
        if task_iri in tasks_map and res_iri in resource_to_producer:
            producer_var = resource_to_producer[res_iri]
            task = tasks_map[task_iri]
            if producer_var != task.var_name and producer_var not in task.context_task_var_names:
                task.context_task_var_names.append(producer_var)


def _extract_workflow(g: Graph, tasks_map: Dict[str, TaskModel]) -> List[WorkflowStepModel]:
    """Extract workflow steps in order."""
    steps: List[WorkflowStepModel] = []
    task_iri_to_var: Dict[str, str] = {t.iri: t.var_name for t in tasks_map.values()}

    for row in g.query(WORKFLOW_QUERY):
        task_iri = _s(row.task)
        task_var = task_iri_to_var.get(task_iri, _safe_var(task_iri))
        order = int(row.stepOrder) if row.stepOrder is not None else len(steps) + 1
        step_type = _s(row.stepType).split("#")[-1]

        steps.append(WorkflowStepModel(
            step_order=order,
            task_var_name=task_var,
            step_type=step_type,
        ))

    # Sort by order
    steps.sort(key=lambda s: s.step_order)
    return steps


def _extract_input_variables(
    g: Graph,
    tasks_map: Dict[str, TaskModel],
    agents_map: Dict[str, AgentModel],
) -> List[InputVariableModel]:
    """Extract all template placeholder variables from prompts and KickoffInputBundle.

    Strategy:
      1. PRIMARY: Query agento-ext:KickoffInputBundle triples (uniform, authoritative).
         If found, use these exclusively — they have key, value, and isDefault flag.
      2. FALLBACK: Legacy extraction from task descriptions + promptInputData +
         Context/Resource descriptions (for TTL files not yet migrated).
    """
    # ── Strategy 1: agento-ext:KickoffInputBundle (primary) ──
    kickoff_results = list(g.query(KICKOFF_INPUTS_QUERY))
    if kickoff_results:
        # Collect all values per key (one key may have multiple example bundles)
        key_data: Dict[str, dict] = {}  # key → {default, is_default, alternatives}
        for row in kickoff_results:
            key = _s(row.key)
            value = _s(row.value)
            is_default_str = _s(row.isDefault).lower()
            is_default = is_default_str in ("true", "1", "yes")

            if key not in key_data:
                key_data[key] = {"default": "", "is_default": False, "alternatives": []}

            if is_default and not key_data[key]["is_default"]:
                # First default wins
                key_data[key]["default"] = value
                key_data[key]["is_default"] = True
            elif value:
                key_data[key]["alternatives"].append(value)

        return [
            InputVariableModel(
                name=key,
                default_value=data["default"],
                has_default=data["is_default"] and bool(data["default"]),
                alternative_values=data["alternatives"],
            )
            for key, data in key_data.items()
        ]

    # ── Strategy 2: Legacy fallback (task descriptions + promptInputData) ──
    all_vars: Dict[str, str] = {}  # name → default_value

    # From task descriptions
    for task in tasks_map.values():
        for var_name in _extract_placeholders(task.description):
            if var_name not in all_vars:
                all_vars[var_name] = ""

    # From prompt input data
    for row in g.query(PROMPT_INPUT_DATA_QUERY):
        text = _s(row.inputData)
        for var_name in _extract_placeholders(text):
            if var_name not in all_vars:
                all_vars[var_name] = ""

    # Try to find default values from :Context / beam:Resource descriptions
    for row in g.query(DEFAULT_INPUTS_QUERY):
        desc = _s(row.desc)
        # Parse lines like "company_stock = 'AMZN'" or "- company_domain: careers.wbd.com"
        for line in desc.split("\n"):
            line = line.strip().lstrip("-").strip()
            # Match "key = value" or "key: value"
            m = re.match(r"(\w+)\s*[:=]\s*(.+)", line)
            if m:
                key = m.group(1).strip()
                val = m.group(2).strip().strip("'\"")
                if key in all_vars:
                    all_vars[key] = val

    return [
        InputVariableModel(name=name, default_value=default, has_default=bool(default))
        for name, default in all_vars.items()
    ]


def _extract_env_vars(g: Graph) -> List[ConfigModel]:
    """Extract environment variable configs (API keys, etc.)."""
    env_vars: List[ConfigModel] = []
    seen: Set[str] = set()
    for row in g.query(ENV_CONFIG_QUERY):
        key = _s(row.key)
        if key not in seen:
            seen.add(key)
            env_vars.append(ConfigModel(key=key, value=_s(row.value)))
    return env_vars


# ─────────────────────── Public API ───────────────────────

def extract_crew_project(file_path: str) -> CrewProject:
    """
    Full SPARQL extraction pipeline for a single KG file.

    Returns a complete CrewProject Pydantic model ready for Layer 3.
    """
    g = load_graph(file_path)

    # 1. Team metadata
    crew_name, description, process = _extract_team(g)
    crew_var_name = _safe_var(crew_name)

    # 2. Language models
    lm_map = _extract_language_models(g)

    # 3. Tools
    tools_map = _extract_tools(g)

    # 4. Agents
    agents_map = _extract_agents(g, tools_map, lm_map)

    # 5. Tasks
    tasks_map = _extract_tasks(g, agents_map)

    # 6. Task context resolution
    _resolve_task_context(g, tasks_map)

    # 7. Workflow ordering
    workflow_steps = _extract_workflow(g, tasks_map)

    # 8. Reorder tasks by workflow
    if workflow_steps:
        step_order = {s.task_var_name: s.step_order for s in workflow_steps}
        task_list = sorted(
            tasks_map.values(),
            key=lambda t: step_order.get(t.var_name, 999),
        )
    else:
        task_list = list(tasks_map.values())

    # 9. Input variables
    input_variables = _extract_input_variables(g, tasks_map, agents_map)

    # 10. Env vars
    env_vars = _extract_env_vars(g)

    project = CrewProject(
        crew_name=crew_name,
        crew_var_name=crew_var_name,
        description=description,
        process=process,
        agents=list(agents_map.values()),
        tasks=task_list,
        tools=list(tools_map.values()),
        workflow_steps=workflow_steps,
        input_variables=input_variables,
        language_models=list(lm_map.values()),
        env_vars=env_vars,
    )

    print(
        f"  [Extracted] crew={crew_name}, "
        f"{len(project.agents)} agents, "
        f"{len(project.tasks)} tasks, "
        f"{len(project.tools)} tools, "
        f"{len(project.workflow_steps)} workflow steps"
    )

    return project
