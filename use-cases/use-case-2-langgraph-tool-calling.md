# UC-2 — Generate a Tool-Calling LangGraph Agent from a Knowledge Graph

## Summary

| Field | Value |
|-------|-------|
| **Actor** | Developer / Researcher using the AgentO generator |
| **Goal** | Turn a Knowledge Graph describing one agent with several tools into a runnable, stateful LangGraph application using the Tool-Calling pattern |
| **Direction** | Forward Engineering (KG → Code) |
| **Framework** | LangGraph |
| **Precondition** | Python 3.10–3.13 environment with `langgraph` + `langchain-core` installed; `generated_kg/LangGraph/trip-planner_instances.ttl` exists |
| **Trigger** | Developer runs the LangGraph generator on a single `.ttl` file |

## Description

LangGraph models workflows as a `StateGraph` of nodes and edges. The generator must
detect which of the three supported patterns the KG represents and emit the right
graph topology. The three patterns are:

| Pattern | Trigger condition | Topology |
|---------|-------------------|----------|
| **Linear** | 1 agent, 0 tools | START → LLM node → END |
| **Tool-Calling** | 1 agent, ≥ 1 tools | agent node ↔ `ToolNode` via `tools_condition` |
| **Supervisor** | > 1 agent | supervisor node routes to worker nodes via `add_conditional_edges` |

In this use case the input KG describes **one agent with four tools**, so the
generator auto-detects the **Tool-Calling** pattern, wraps each tool with the `@tool`
decorator, binds them with `llm.bind_tools(...)`, and wires the conditional routing.

## Input

**Command:**
```bash
python src/langgraph/run.py generated_kg/LangGraph/trip-planner_instances.ttl
```

**Source data:** A Knowledge Graph defining a single `:LLMAgent` and four `:Tool`
instances (`extract`, `classify`, `list_accommodations`, `list_restaurants`) connected
through `:WorkflowStep` / `:nextStep` relationships.

## Output

**Console output (pattern auto-detection):**
```
Reading KG from generated_kg/LangGraph/trip-planner_instances.ttl...
Detected LangGraph Pattern: tool_calling
- Extracted 1 Agent(s)
- Extracted 4 Tool(s)
- Extracted 4 Node(s)
Generating Python code into output_files/langgraph/trip-planner...
Done!
```

**Generated project directory:** `output_files/langgraph/trip-planner/`

```
output_files/langgraph/trip-planner/
├── main.py             # StateGraph + @tool fns + bind_tools + ToolNode
├── config/
│   └── inputs.yaml     # runtime inputs
├── .env.example
├── requirements.txt
└── manifest.json
```

**Runtime input the generated app consumes — `config/inputs.yaml`:**
```yaml
location: "Bali, Indonesia"
startDate: "2026-08-15"
endDate: "2026-08-22"
numberOfGuests: 2
interests: "beaches, temples, local food"
```

**Representative output — the four tools surfaced in `main.py`:**
The generated script defines four `@tool` functions matching the KG exactly:
`extract`, `classify`, `list_accommodations`, `list_restaurants`. These are bound to
the LLM and exposed to the graph through a `ToolNode`.

## Result / Postcondition

- A runnable LangGraph project is written to `output_files/langgraph/trip-planner/`.
- Pattern detection is correct (`tool_calling`), and the generated tool set matches the
  IR exactly (4/4 tools, named, no leaks) — see `trip-planner` row in
  `docs/quality_report.md` (**score 100.0/100**) and `docs/summary_statistics.md`
  (73 LOC, ✅ syntax pass).
- After supplying an `OPENAI_API_KEY` (copy `.env.example` → `.env`), the developer runs:
  ```bash
  cd output_files/langgraph/trip-planner
  pip install -r requirements.txt
  python main.py
  ```

## Notes & Limitations

- All 9 LangGraph scenarios compile and pass offline validation (9/9, 100%) — see
  `docs/validation_results.md`.
- LangGraph conditional-edge routing logic and strict `TypedDict`/`zod` schemas cannot
  be fully represented in the ontology; they are reduced to descriptive strings — see
  `docs/#02 langgraph-pipeline-analysis.md`.
- To generate **all** LangGraph projects at once (PowerShell):
  ```powershell
  Get-ChildItem generated_kg\LangGraph\*.ttl | ForEach-Object {
      python src/langgraph/run.py $_.FullName
  }
  ```
