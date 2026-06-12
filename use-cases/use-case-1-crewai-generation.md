# UC-1 — Generate a Runnable CrewAI Project from a Knowledge Graph

## Summary

| Field | Value |
|-------|-------|
| **Actor** | Developer / Researcher using the AgentO generator |
| **Goal** | Turn a semantic Knowledge Graph describing a multi-agent crew into a complete, runnable CrewAI Python project |
| **Direction** | Forward Engineering (KG → Code) |
| **Framework** | CrewAI |
| **Precondition** | Python 3.10–3.13 environment with dependencies installed (`pip install -r requirements.txt`); the file `generated_kg/CrewAI/trip_planner_instances.ttl` exists |
| **Trigger** | Developer runs the CrewAI generator on a single `.ttl` file |

## Description

The developer has a Knowledge Graph (`trip_planner_instances.ttl`) that semantically
describes a travel-planning crew using the **AgentO ontology** — three agents (a City
Selection Expert, a Local Expert, and a Travel Concierge), their tasks, and a
sequential workflow. Rather than hand-writing the CrewAI boilerplate, the developer
runs the generator, which:

1. **Layer 1 (Extraction)** — `src/crewai/extractor.py` runs SPARQL queries over the
   `.ttl` graph, reading `:Team`, `:LLMAgent`, `:Task`, `:Tool`, and `:nextStep`
   relationships.
2. **Layer 2 (IR)** — the extracted entities are validated into typed Pydantic
   models (`src/crewai/models.py`).
3. **Layer 3 (Generation)** — `src/crewai/generator.py` renders the IR into
   `agents.yaml`, `tasks.yaml`, and Jinja2-based `crew.py` / `main.py`.

## Input

**Command:**
```bash
python -m src.crewai.run generated_kg/CrewAI/trip_planner_instances.ttl
```

**Source data (excerpt of the input Knowledge Graph, AgentO Turtle):**
The KG defines a crew whose agents map to roles/goals. The extractor reads, among
others, the `city_selection_agent` with its role *"City Selection Expert"* and goal
*"Select the best city based on weather patterns, seasonal events, and travel costs."*

## Output

**Generated project directory:** `output_files/crewai/trip_planner/`

```
output_files/crewai/trip_planner/
├── config/
│   ├── agents.yaml      # 3 agents with role/goal/backstory
│   ├── tasks.yaml       # tasks linked to agents
│   └── inputs.yaml      # runtime inputs for crew.kickoff()
├── crew.py              # @crew / @agent / @task definitions
├── main.py              # kickoff entry point
├── .env.example
├── pyproject.toml
└── manifest.json
```

**Representative output — `config/agents.yaml`:**
```yaml
city_selection_agent:
  role: City Selection Expert
  goal: Select the best city based on weather patterns, seasonal events, and travel costs
  backstory: You are a City Selection Expert.
local_expert_agent:
  role: Local Expert at this city
  goal: Provide in-depth local guide content, hidden gems, and practical tips.
  backstory: You are a Local Expert at this city.
travel_concierge_agent:
  role: Amazing Travel Concierge
  goal: |
    Create a 7-day travel itinerary with detailed daily plans, budgets, packing suggestions, and logistics.
  backstory: You are a Amazing Travel Concierge.
```

**Runtime input the generated crew consumes — `config/inputs.yaml`:**
```yaml
origin: ""      # required — provide a value before running
cities: ""      # required — provide a value before running
range: ""       # required — provide a value before running
interests: ""   # required — provide a value before running
```

## Result / Postcondition

- A complete, syntactically valid CrewAI project is written to
  `output_files/crewai/trip_planner/`.
- The project follows the official CrewAI layout (YAML configs + `crew.py` + `main.py`)
  and is confirmed to compile (`✅ Pass` in `docs/summary_statistics.md`, 107 LOC,
  3 agents / 3 tasks / 3 tools).
- After filling `config/inputs.yaml` and providing an `OPENAI_API_KEY`, the developer
  can execute the crew:
  ```bash
  cd output_files/crewai/trip_planner
  python main.py
  ```

## Notes & Limitations

- Batch mode (`python -m src.crewai.run`, no argument) generates all 17 CrewAI
  scenarios at once; overall CrewAI compilation rate is 12/17 (70.6%) — see
  `docs/summary_statistics.md` for the per-scenario breakdown and known
  syntax-failure cases (e.g. `gym_planner`, `markdown_validator`).
- Direct agent-to-agent links (`:interactsWith`) and resource artifacts
  (`:producedResource`) present in the ontology are not yet mapped into CrewAI
  output — see `docs/#01 crewai-pipeline-analysis.md`.
