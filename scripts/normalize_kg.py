"""
Normalize all CrewAI KG TTL files to canonical agent pattern.

Canonical pattern per LLMAgent (following agentO.ttl ontology):
  - :agentRole          → role literal (DatatypeProperty on LLMAgent)
  - :hasAgentGoal       → Goal individual with dcterms:description = goal text
  - :agentPrompt        → Prompt with :promptContext = backstory text
                           (ontology: "The context or background information for the prompt")
  - :hasAgentConfig     → 1 Config individual per runtime param (allow_delegation, verbose)

NOT canonical (removed during normalization):
  - role/goal/backstory in :Config nodes (Config is for runtime params only)
  - role/goal/backstory in :promptInstruction (instruction ≠ persona)
  - role/goal/backstory in dcterms:description on agent (description ≠ backstory)
  - merged "role: X; goal: Y; backstory: Z" strings in :promptContext

What this script does:
  1. Parse each TTL with rdflib
  2. Extract role/goal/backstory from all known locations (Config, Prompt, Goal, desc blobs)
  3. Rewrite agent, config, prompt, and goal triples in canonical form
  4. Preserve all non-agent triples (tasks, workflows, resources, teams, etc.) as-is
"""

import re
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, RDF, RDFS
from rdflib.namespace import DCTERMS

ONTO = Namespace("http://www.w3id.org/agentic-ai/onto#")

KG_DIR = Path(__file__).resolve().parent.parent / "generated_kg" / "CrewAI"


def _s(val) -> str:
    return str(val).strip() if val else ""


def _local(iri: str) -> str:
    """Extract local name from IRI (after # or last /)."""
    if "#" in iri:
        return iri.split("#")[-1]
    return iri.rsplit("/", 1)[-1]


def _parse_labeled_block(text: str) -> dict:
    """
    Parse text with labeled fields like:
      Role: Some Role
      Goal: Some Goal
      Backstory: Some Backstory
    Returns dict with lowercase keys.
    """
    result = {}
    if not text:
        return result
    # Match patterns like "Role: ...", "Goal: ...", "Backstory: ..."
    # Handle multiline values by using lookahead for next label or end
    labels = ["role", "goal", "backstory", "tools", "allowdelegation",
              "allow_delegation", "verbose", "usage", "notes"]
    pattern = "|".join(re.escape(l) for l in labels)
    parts = re.split(rf"(?i)(?:^|\n)\s*({pattern})\s*:\s*", text)
    # parts = ['prefix', 'label1', 'value1', 'label2', 'value2', ...]
    if len(parts) >= 3:
        for i in range(1, len(parts) - 1, 2):
            key = parts[i].strip().lower().replace(" ", "_")
            val = parts[i + 1].strip()
            if key and val:
                result[key] = val
    return result


def _parse_semicolon_block(text: str) -> dict:
    """Parse 'role: X; goal: Y; backstory: Z' format."""
    result = {}
    if not text:
        return result
    parts = re.split(r";\s*", text)
    for part in parts:
        m = re.match(r"(\w+)\s*:\s*(.+)", part.strip(), re.DOTALL)
        if m:
            result[m.group(1).lower()] = m.group(2).strip()
    return result


def _extract_config_kv_via_rdflib(g: Graph, cfg_iri_str: str) -> list:
    """
    Extract (key, value) pairs from a Config node using rdflib graph API.
    Handles all Turtle string formats including triple-quoted strings.
    For single-KV Config nodes (Pattern I), returns exactly one pair.
    For multi-KV Config nodes (Pattern C), returns all combinations
    but marks them as potentially unpaired.
    """
    cfg_uri = URIRef(cfg_iri_str)
    keys = [_s(o) for o in g.objects(cfg_uri, ONTO.configKey)]
    values = [_s(o) for o in g.objects(cfg_uri, ONTO.configValue)]

    if len(keys) == 1 and len(values) == 1:
        # Pattern I: single KV pair — perfectly paired
        return [(keys[0], values[0])]
    elif len(keys) == len(values) == 0:
        return []
    else:
        # Multi-KV node: we can't reliably pair them via rdflib alone.
        # Return all keys and values; caller must handle Cartesian ambiguity.
        # For now, zip by index (best effort — works if order is preserved).
        if len(keys) == len(values):
            return list(zip(keys, values))
        # Mismatched counts — return nothing to avoid wrong pairings
        return []


def extract_agent_data(g: Graph, raw_ttl: str) -> dict:
    """
    Extract complete agent data from all possible locations in the KG.
    Returns {agent_iri: {role, goal, backstory, allow_delegation, verbose,
             goal_iri, config_iris, prompt_iri, lm_iris, tool_iris,
             capability_iris, label, agent_id, other_props, ...}}
    """
    agents = {}

    # Find all LLMAgent individuals
    for agent_uri in g.subjects(RDF.type, ONTO.LLMAgent):
        iri = str(agent_uri)
        data = {
            "iri": iri,
            "local": _local(iri),
            "label": "",
            "agent_id": "",
            "role": "",
            "goal": "",
            "backstory": "",
            "allow_delegation": None,
            "verbose": None,
            "goal_iri": None,
            "goal_title": "",
            "config_iris": [],
            "prompt_iri": None,
            "lm_iris": [],
            "tool_iris": [],
            "capability_iris": [],
            "knowledge_iris": [],
            "interacts_iris": [],
            "operates_in": None,
            "comment": "",
            "title": "",
            # Prompt data to preserve
            "prompt_instruction": "",
            "prompt_output_indicator": "",
            "prompt_input_data": "",
            "prompt_label": "",
        }

        # Direct properties on agent node
        for p, o in g.predicate_objects(agent_uri):
            ps = str(p)
            os = _s(o)
            if ps == str(RDFS.label):
                data["label"] = os
            elif ps == str(ONTO.agentID):
                data["agent_id"] = os
            elif ps == str(ONTO.agentRole):
                data["role"] = os
            elif ps == str(DCTERMS.description):
                data["desc_on_agent"] = os
            elif ps == str(DCTERMS.title):
                data["title"] = os
            elif ps == str(RDFS.comment):
                data["comment"] = os
            elif ps == str(ONTO.hasAgentGoal):
                data["goal_iri"] = os
            elif ps == str(ONTO.hasAgentConfig):
                data["config_iris"].append(os)
            elif ps == str(ONTO.agentPrompt) or ps == str(ONTO.hasPrompt):
                data["prompt_iri"] = os
            elif ps == str(ONTO.useLanguageModel):
                data["lm_iris"].append(os)
            elif ps == str(ONTO.agentToolUsage):
                data["tool_iris"].append(os)
            elif ps == str(ONTO.hasAgentCapability):
                data["capability_iris"].append(os)
            elif ps == str(ONTO.hasKnowledge):
                data["knowledge_iris"].append(os)
            elif ps == str(ONTO.interactsWith):
                data["interacts_iris"].append(os)
            elif ps == str(ONTO.operatesIn):
                data["operates_in"] = os

        # --- Extract role/goal/backstory from all sources ---
        # Priority: Config (verbatim from source YAML) > Goal individual (may be GPT-paraphrased)
        #         > Prompt fields > dcterms:description blob

        # Source 1: Config KV pairs (verbatim — highest priority)
        # Use rdflib graph API instead of regex to handle triple-quoted strings
        for cfg_iri in data["config_iris"]:
            kv_pairs = _extract_config_kv_via_rdflib(g, cfg_iri)
            for k, v in kv_pairs:
                kl = k.lower()
                if kl == "goal":
                    # Config goal is verbatim — always prefer over Goal individual
                    data["goal"] = v
                elif kl == "backstory" and not data["backstory"]:
                    data["backstory"] = v
                elif kl == "role" and not data["role"]:
                    data["role"] = v
                elif kl == "allow_delegation" and data["allow_delegation"] is None:
                    data["allow_delegation"] = v.lower() in ("true", "1", "yes")
                elif kl == "verbose" and data["verbose"] is None:
                    val = v.lower()
                    if val in ("false", "0", "no", "none"):
                        data["verbose"] = False
                    else:
                        data["verbose"] = True

        # Source 2: Goal individual (fallback if Config didn't have goal)
        if not data["goal"] and data["goal_iri"]:
            goal_uri = URIRef(data["goal_iri"])
            for p, o in g.predicate_objects(goal_uri):
                ps = str(p)
                if ps == str(DCTERMS.description):
                    data["goal"] = _s(o)
                elif ps == str(DCTERMS.title):
                    data["goal_title"] = _s(o)
        # Always grab the goal title if available (even if goal text came from Config)
        if data["goal_iri"] and not data["goal_title"]:
            goal_uri = URIRef(data["goal_iri"])
            for o in g.objects(goal_uri, DCTERMS.title):
                data["goal_title"] = _s(o)

        # Source 3: Prompt
        if data["prompt_iri"]:
            prompt_uri = URIRef(data["prompt_iri"])
            prompt_ctx = ""
            prompt_instr = ""
            for p, o in g.predicate_objects(prompt_uri):
                ps = str(p)
                os = _s(o)
                if ps == str(ONTO.promptContext):
                    prompt_ctx = os
                elif ps == str(ONTO.promptInstruction):
                    prompt_instr = os
                    data["prompt_instruction"] = os
                elif ps == str(ONTO.promptOutputIndicator):
                    data["prompt_output_indicator"] = os
                elif ps == str(ONTO.promptInputData):
                    data["prompt_input_data"] = os
                elif ps == str(RDFS.label):
                    data["prompt_label"] = os

            # Try to parse labeled fields from promptInstruction
            parsed = _parse_labeled_block(prompt_instr)
            if not data["goal"] and "goal" in parsed:
                data["goal"] = parsed["goal"]
            if not data["backstory"] and "backstory" in parsed:
                data["backstory"] = parsed["backstory"]
            if not data["role"] and "role" in parsed:
                data["role"] = parsed["role"]
            if data["allow_delegation"] is None and "allow_delegation" in parsed:
                data["allow_delegation"] = parsed["allow_delegation"].lower() in ("true", "1", "yes")
            if data["verbose"] is None and "verbose" in parsed:
                val = parsed["verbose"].lower()
                data["verbose"] = val not in ("false", "0", "no", "none")

            # Try promptContext (semicolon-separated or labeled)
            parsed_ctx = _parse_semicolon_block(prompt_ctx)
            if not parsed_ctx:
                parsed_ctx = _parse_labeled_block(prompt_ctx)
            if not data["goal"] and "goal" in parsed_ctx:
                data["goal"] = parsed_ctx["goal"]
            if not data["backstory"] and "backstory" in parsed_ctx:
                data["backstory"] = parsed_ctx["backstory"]

            # Source 3b: If backstory still empty and promptInstruction exists,
            # use it as backstory (in many KGs, backstory = promptInstruction)
            if not data["backstory"] and prompt_instr:
                data["backstory"] = prompt_instr

        # Source 4: dcterms:description on agent node (blob)
        desc = data.get("desc_on_agent", "")
        if desc:
            parsed_desc = _parse_labeled_block(desc)
            if not data["goal"] and "goal" in parsed_desc:
                data["goal"] = parsed_desc["goal"]
            if not data["backstory"] and "backstory" in parsed_desc:
                data["backstory"] = parsed_desc["backstory"]
            # If not parsed as labeled, and backstory is still empty,
            # use the whole description if it looks like a backstory
            if not data["backstory"] and not parsed_desc:
                # If desc doesn't start with "Agent " or similar generic prefix,
                # it might be the backstory itself
                pass  # We'll handle this after all sources

        # Source 5: For agents where dcterms:description on agent IS the backstory
        # (industry-agents, starter_template, trip_planner patterns)
        if not data["backstory"] and desc:
            # If the description starts with "backstory:" prefix, extract it
            m = re.match(r"(?i)backstory\s*:\s*(.+)", desc, re.DOTALL)
            if m:
                data["backstory"] = m.group(1).strip()
            # If it's a short descriptive sentence that's agent-describing
            # (not a blob with multiple fields), it's likely the backstory
            elif not any(kw in desc.lower() for kw in ["role:", "goal:", "tools:", "allowdelegation:"]):
                data["backstory"] = desc

        # Final defaults
        if not data["role"]:
            data["role"] = data["label"] or data["agent_id"] or "Agent"
        if not data["goal"]:
            data["goal"] = data["role"]
        if not data["backstory"]:
            data["backstory"] = f"You are a {data['role']}."

        agents[iri] = data

    return agents


def detect_prefix_style(raw_ttl: str) -> dict:
    """Detect which prefix conventions the file uses."""
    style = {
        "dcterms_prefix": "dcterms",
        "rdf_type_shorthand": True,  # use 'a' vs 'rdf:type'
    }
    if "@prefix dct:" in raw_ttl:
        style["dcterms_prefix"] = "dct"
    elif "@prefix dcterms:" in raw_ttl:
        style["dcterms_prefix"] = "dcterms"
    elif "<http://purl.org/dc/terms/" in raw_ttl and "@prefix" not in raw_ttl.split("<http://purl.org/dc/terms/")[0].split("\n")[-1]:
        style["dcterms_prefix"] = "_full_uri"

    if "rdf:type" in raw_ttl:
        style["rdf_type_shorthand"] = False

    return style


def is_agent_related(g: Graph, subj_uri: URIRef, agent_iris: set, agent_config_iris: set,
                     agent_prompt_iris: set, agent_goal_iris: set) -> bool:
    """Check if a subject URI is an agent, agent's config, prompt, or goal that we'll rewrite."""
    s = str(subj_uri)
    return (s in agent_iris or s in agent_config_iris or
            s in agent_prompt_iris or s in agent_goal_iris)


def rebuild_ttl(file_path: Path) -> str:
    """
    Parse a TTL file and rebuild it with canonical agent patterns.
    Non-agent content is preserved as-is from the raw text.
    """
    raw = file_path.read_text(encoding="utf-8")
    g = Graph()
    g.parse(str(file_path), format="turtle")

    agents = extract_agent_data(g, raw)
    if not agents:
        print(f"  No agents found in {file_path.name}, skipping.")
        return raw

    style = detect_prefix_style(raw)
    dct = style["dcterms_prefix"]

    # Collect IRIs of all agent-related individuals that we'll rewrite
    agent_iris = set(agents.keys())
    agent_config_iris = set()
    agent_prompt_iris = set()
    agent_goal_iris = set()

    for a in agents.values():
        agent_config_iris.update(a["config_iris"])
        if a["prompt_iri"]:
            agent_prompt_iris.add(a["prompt_iri"])
        if a["goal_iri"]:
            agent_goal_iris.add(a["goal_iri"])

    # Check for goals shared across agents (don't blindly rewrite shared goals)
    goal_usage_count = {}
    for a in agents.values():
        if a["goal_iri"]:
            goal_usage_count[a["goal_iri"]] = goal_usage_count.get(a["goal_iri"], 0) + 1

    # For shared goals where agents have different actual goals, create new per-agent goals
    # For shared goals where agents truly share the goal, keep the shared goal
    goal_rewrites = {}  # agent_iri -> new_goal_local_name
    for a_iri, a in agents.items():
        if a["goal_iri"] and goal_usage_count.get(a["goal_iri"], 0) > 1:
            # Check if this agent's extracted goal differs from the Goal individual's description
            goal_uri = URIRef(a["goal_iri"])
            goal_desc = ""
            for p, o in g.predicate_objects(goal_uri):
                if str(p) == str(DCTERMS.description):
                    goal_desc = _s(o)
            if a["goal"] and goal_desc and a["goal"] != goal_desc:
                # Different goal text → need a new Goal individual
                goal_rewrites[a_iri] = f"goal_{a['local']}"

    # === Build the new file content ===

    lines = raw.split("\n")

    # Collect leading @prefix / @base lines; the first comment line ends the block.
    prefix_lines = []
    in_prefix = True
    for line in lines:
        stripped = line.strip()
        if in_prefix and (stripped.startswith("@prefix") or stripped.startswith("@base")):
            prefix_lines.append(line)
        elif stripped.startswith("#") or stripped == "":
            if stripped.startswith("#"):
                in_prefix = False
        else:
            break

    # === Build output ===
    output_parts = []

    # 1. Prefixes
    output_parts.append("\n".join(prefix_lines))
    output_parts.append("")

    # 2. Comment header - preserve execution time, model, issues block from original
    # Find the comment block between prefixes and first triple
    raw_after_prefix = raw
    for pl in prefix_lines:
        idx = raw_after_prefix.find(pl)
        if idx >= 0:
            raw_after_prefix = raw_after_prefix[idx + len(pl):]
    # Extract comment block
    comment_block_lines = []
    for line in raw_after_prefix.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or stripped == "":
            comment_block_lines.append(line)
        else:
            break
    if comment_block_lines:
        output_parts.append("\n".join(comment_block_lines))

    # 3. Non-agent content - extract from raw text by finding blocks
    # We need to preserve non-agent blocks in their original form.
    # Let's use a regex approach to find all TTL blocks and classify them.

    # Parse the raw TTL into blocks (each block = one subject's triples ending with .)
    # This is a simplified TTL block parser
    non_agent_blocks = extract_non_agent_blocks(raw, agent_iris, agent_config_iris,
                                                  agent_prompt_iris, agent_goal_iris)

    if non_agent_blocks:
        output_parts.append("")
        output_parts.append(non_agent_blocks)

    # 4. Canonical agent sections
    output_parts.append("")
    output_parts.append("#################################################################")
    output_parts.append("# Agents (Canonical Pattern)")
    output_parts.append("#################################################################")

    # Determine formatting helpers
    type_kw = "a" if style["rdf_type_shorthand"] else "rdf:type"

    # Collect all goals we need to emit (shared + new per-agent)
    goals_to_emit = {}  # goal_local -> {title, description, original_iri}

    for a_iri, a in agents.items():
        if a_iri in goal_rewrites:
            # New per-agent goal
            gl = goal_rewrites[a_iri]
            goals_to_emit[gl] = {
                "title": a.get("goal_title", "") or f"{a['label'] or a['agent_id']} goal",
                "description": a["goal"],
            }
        elif a["goal_iri"]:
            gl = _local(a["goal_iri"])
            if gl not in goals_to_emit:
                goals_to_emit[gl] = {
                    "title": a.get("goal_title", ""),
                    "description": a["goal"],
                }

    # Emit Goal individuals
    output_parts.append("")
    output_parts.append("# Goals")
    for gl, gdata in goals_to_emit.items():
        desc_prop = f"{dct}:description" if dct != "_full_uri" else "<http://purl.org/dc/terms/description>"
        title_prop = f"{dct}:title" if dct != "_full_uri" else "<http://purl.org/dc/terms/title>"

        block = f"\n:{gl} {type_kw} :Goal"
        if gdata["title"]:
            block += f" ;\n    {title_prop} {_ttl_str(gdata['title'])}"
        block += f" ;\n    {desc_prop} {_ttl_str(gdata['description'])} ."
        output_parts.append(block)

    # Emit Agent + Config + Prompt for each agent
    for a_iri, a in agents.items():
        output_parts.append("")

        # Determine goal IRI to use
        if a_iri in goal_rewrites:
            goal_ref = f":{goal_rewrites[a_iri]}"
        elif a["goal_iri"]:
            goal_ref = f":{_local(a['goal_iri'])}"
        else:
            # Create a new goal
            new_goal_local = f"goal_{a['local']}"
            goal_ref = f":{new_goal_local}"
            goals_to_emit[new_goal_local] = {
                "title": f"{a['label'] or a['agent_id']} goal",
                "description": a["goal"],
            }
            # Insert the goal block before this agent
            desc_prop = f"{dct}:description" if dct != "_full_uri" else "<http://purl.org/dc/terms/description>"
            title_prop = f"{dct}:title" if dct != "_full_uri" else "<http://purl.org/dc/terms/title>"
            gdata = goals_to_emit[new_goal_local]
            goal_block = f":{new_goal_local} {type_kw} :Goal"
            if gdata["title"]:
                goal_block += f" ;\n    {title_prop} {_ttl_str(gdata['title'])}"
            goal_block += f" ;\n    {desc_prop} {_ttl_str(gdata['description'])} ."
            output_parts.append(goal_block)
            output_parts.append("")

        desc_prop = f"{dct}:description" if dct != "_full_uri" else "<http://purl.org/dc/terms/description>"

        # Agent block
        agent_local = a["local"]
        block_lines = [f":{agent_local} {type_kw} :LLMAgent ;"]
        if a["label"]:
            block_lines.append(f'    rdfs:label {_ttl_str(a["label"])} ;')
        if a["agent_id"]:
            block_lines.append(f'    :agentID {_ttl_str(a["agent_id"])} ;')
        block_lines.append(f'    :agentRole {_ttl_str(a["role"])} ;')
        block_lines.append(f"    :hasAgentGoal {goal_ref} ;")

        # Config individuals for allow_delegation and verbose
        config_refs = []
        if a["allow_delegation"] is not None:
            cfg_name = f"cfg_{agent_local}_delegation"
            config_refs.append(f":{cfg_name}")
        if a["verbose"] is not None:
            cfg_name = f"cfg_{agent_local}_verbose"
            config_refs.append(f":{cfg_name}")
        if config_refs:
            block_lines.append(f'    :hasAgentConfig {" , ".join(config_refs)} ;')

        # Capabilities
        if a["capability_iris"]:
            caps = " , ".join(f":{_local(c)}" for c in a["capability_iris"])
            block_lines.append(f"    :hasAgentCapability {caps} ;")

        # Tools
        if a["tool_iris"]:
            tools = " , ".join(f":{_local(t)}" for t in a["tool_iris"])
            block_lines.append(f"    :agentToolUsage {tools} ;")

        # Language models
        if a["lm_iris"]:
            lms = " , ".join(f":{_local(lm)}" for lm in a["lm_iris"])
            block_lines.append(f"    :useLanguageModel {lms} ;")

        # Knowledge
        if a["knowledge_iris"]:
            kbs = " , ".join(f":{_local(k)}" for k in a["knowledge_iris"])
            block_lines.append(f"    :hasKnowledge {kbs} ;")

        # InteractsWith
        if a["interacts_iris"]:
            ints = " , ".join(f":{_local(i)}" for i in a["interacts_iris"])
            block_lines.append(f"    :interactsWith {ints} ;")

        # OperatesIn
        if a["operates_in"]:
            block_lines.append(f"    :operatesIn :{_local(a['operates_in'])} ;")

        # Prompt
        prompt_local = f"prompt_{agent_local}"
        block_lines.append(f"    :agentPrompt :{prompt_local} .")

        output_parts.append("\n".join(block_lines))

        # Config individuals
        if a["allow_delegation"] is not None:
            cfg_name = f"cfg_{agent_local}_delegation"
            val = "True" if a["allow_delegation"] else "False"
            output_parts.append(
                f'\n:{cfg_name} {type_kw} :Config ;\n'
                f'    :configKey "allow_delegation" ;\n'
                f'    :configValue "{val}" .'
            )
        if a["verbose"] is not None:
            cfg_name = f"cfg_{agent_local}_verbose"
            val = "True" if a["verbose"] else "False"
            output_parts.append(
                f'\n:{cfg_name} {type_kw} :Config ;\n'
                f'    :configKey "verbose" ;\n'
                f'    :configValue "{val}" .'
            )

        # Prompt individual — backstory goes to :promptContext (ontology canonical)
        prompt_lines = [f"\n:{prompt_local} {type_kw} :Prompt ;"]
        if a["prompt_label"]:
            prompt_lines.append(f'    rdfs:label {_ttl_str(a["prompt_label"])} ;')
        # Backstory = :promptContext ("The context or background information for the prompt")
        prompt_lines.append(f'    :promptContext {_ttl_str(a["backstory"])} ;')
        # Fix last semicolon to period
        if prompt_lines:
            prompt_lines[-1] = prompt_lines[-1].rstrip(" ;") + " ."
        output_parts.append("\n".join(prompt_lines))

    # Ensure trailing newline
    result = "\n".join(output_parts)
    if not result.endswith("\n"):
        result += "\n"
    return result


def _ttl_str(s: str) -> str:
    """Format a string as a Turtle literal, using triple quotes if multiline."""
    if not s:
        return '""'
    if "\n" in s or '"' in s:
        # Use triple-quoted string
        escaped = s.replace("\\", "\\\\")
        return f'"""{escaped}"""'
    return f'"{s}"'


def extract_non_agent_blocks(raw: str, agent_iris: set, config_iris: set,
                              prompt_iris: set, goal_iris: set) -> str:
    """
    Extract all TTL blocks from raw text that are NOT about agents, their configs,
    prompts, or goals. Returns the concatenated non-agent blocks.
    """
    # Build set of local names to filter out
    skip_locals = set()
    for iri in (agent_iris | config_iris | prompt_iris | goal_iris):
        skip_locals.add(_local(iri))

    # Split raw TTL into blocks. A block starts with a subject declaration
    # and ends with a period followed by newline (possibly with blank lines).
    # We use a regex that matches TTL statement blocks.

    # First, strip prefix declarations and comments at the top
    lines = raw.split("\n")
    content_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if (stripped.startswith("@prefix") or stripped.startswith("@base") or
                stripped.startswith("#") or stripped == ""):
            content_start = i + 1
        else:
            break

    content = "\n".join(lines[content_start:])

    # Split into blocks at points where a new subject starts
    # A new subject starts at column 0 with :something or <something>
    block_pattern = re.compile(r'^(:[a-zA-Z_][\w.-]*|<[^>]+>)\s', re.MULTILINE)

    blocks = []
    positions = [m.start() for m in block_pattern.finditer(content)]
    positions.append(len(content))

    non_agent_blocks = []
    for i in range(len(positions) - 1):
        block = content[positions[i]:positions[i + 1]].strip()
        if not block:
            continue

        # Extract the subject local name from this block
        m = re.match(r':([a-zA-Z_][\w.-]*)', block)
        if m:
            local = m.group(1)
            if local in skip_locals:
                continue

        # Also check full URI subjects
        m2 = re.match(r'<([^>]+)>', block)
        if m2:
            full_iri = m2.group(1)
            if _local(full_iri) in skip_locals:
                continue

        non_agent_blocks.append(block)

    return "\n\n".join(non_agent_blocks)


def normalize_file(file_path: Path) -> None:
    """Normalize a single KG TTL file."""
    print(f"Processing: {file_path.name}")
    try:
        new_content = rebuild_ttl(file_path)
        file_path.write_text(new_content, encoding="utf-8")
        print(f"  Done: {file_path.name}")
    except Exception as e:
        print(f"  ERROR in {file_path.name}: {e}")
        import traceback
        traceback.print_exc()


def main():
    files = sorted(KG_DIR.glob("*_instances.ttl"))
    print(f"Found {len(files)} TTL files in {KG_DIR}")

    for f in files:
        normalize_file(f)

    print("\nAll files processed.")


if __name__ == "__main__":
    main()
