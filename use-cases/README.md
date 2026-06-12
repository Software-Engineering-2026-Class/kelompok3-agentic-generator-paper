# Use Cases — Agentic AI Framework Generator (AgentO)

This folder documents concrete end-to-end use cases of the AgentO generator. Each
use case states the **actor**, the **input** (the exact command and source data),
and the **output** (the artifacts produced and a representative result), together
with a short description of what happens at each pipeline layer.

All examples below are reproducible from the repository root using the knowledge
graphs already committed under `generated_kg/` and the projects already generated
under `output_files/`.

| # | Use Case | Direction | Framework | Input | Output |
|---|----------|-----------|-----------|-------|--------|
| [UC-1](use-case-1-crewai-generation.md) | Generate a runnable CrewAI project from a Knowledge Graph | Forward (KG → Code) | CrewAI | `trip_planner_instances.ttl` | `agents.yaml`, `tasks.yaml`, `crew.py`, `main.py` |
| [UC-2](use-case-2-langgraph-tool-calling.md) | Generate a Tool-Calling LangGraph agent from a Knowledge Graph | Forward (KG → Code) | LangGraph | `trip-planner_instances.ttl` | `main.py`, `requirements.txt`, `manifest.json` |
| [UC-3](use-case-3-quality-evaluation.md) | Evaluate generated code quality offline (no API key) | Quality Assurance | LangGraph | 9 generated projects | `quality_report.md` (avg score 93.3/100) |

## How These Use Cases Relate to the Pipeline

```
KG (.ttl)  ──►  Layer 1: SPARQL Extraction  ──►  Layer 2: Pydantic IR  ──►  Layer 3: Jinja2 Codegen  ──►  Runnable Project
                                                                                                              │
                                                                                                              ▼
                                                                                          UC-3: Offline Quality Evaluation
```

- **UC-1** and **UC-2** exercise the **forward engineering** path (Layers 1–3) for the
  two target frameworks.
- **UC-3** exercises the **offline evaluation** path that scores every generated
  LangGraph project without requiring an OpenAI API key.

> Reverse engineering (Code → KG via OpenAI LLM) is described in the main
> [`README.md`](../README.md#3-reverse-engineering--code-to-kg); it requires an
> active API key and is therefore not included as a reproducible offline use case here.
