# Generator Summary Statistics Report

This report provides summary statistics for the generated code across two agentic AI frameworks: **LangGraph** and **CrewAI**.

## Framework-Level Performance Comparison

| Metric | LangGraph | CrewAI | Total Aggregated |
| --- | --- | --- | --- |
| **KG Patterns / Scenarios Processed** | 9 | 17 | 26 |
| **Generated Agents** | 8 | 52 | 60 |
| **Generated Tasks** | 17 | 60 | 77 |
| **Generated Tools** | 22 | 42 | 64 |
| **Lines of Code (LOC) Generated** | 362 | 1967 | 2329 |
| **Correctness (Compilation Rate)** | 9/9 (100.0%) | 13/17 (76.5%) | 22/26 (84.6%) |

## LangGraph Scenarios Detailed Statistics

| Scenario Name | Detected KG Pattern | Agents | Tasks / Nodes | Tools | Generated LOC | Correctness (Syntax) |
| --- | --- | --- | --- | --- | --- | --- |
| `chat-agent` | `linear` | 1 | 1 | 0 | 21 | ✅ Pass |
| `email-agent` | `tool_calling` | 1 | 3 | 1 | 32 | ✅ Pass |
| `open-code` | `tool_calling` | 1 | 2 | 2 | 36 | ✅ Pass |
| `pizza-orderer` | `tool_calling` | 1 | 1 | 2 | 36 | ✅ Pass |
| `stockbroker` | `tool_calling` | 1 | 1 | 3 | 40 | ✅ Pass |
| `supervisor` | `tool_calling` | 1 | 1 | 7 | 56 | ✅ Pass |
| `trip-planner` | `tool_calling` | 1 | 4 | 4 | 73 | ✅ Pass |
| `utils` | `tool_calling` | 0 | 2 | 2 | 36 | ✅ Pass |
| `writer-agent` | `tool_calling` | 1 | 2 | 1 | 32 | ✅ Pass |

## CrewAI Scenarios Detailed Statistics

| Scenario Name | Process Pattern | Agents | Tasks | Tools | Generated LOC | Correctness (Syntax) |
| --- | --- | --- | --- | --- | --- | --- |
| `game-builder-crew` | `sequential` | 3 | 3 | 0 | 106 | ✅ Pass |
| `gym_planner` | `sequential` | 2 | 2 | 1 | 94 | ✅ Pass |
| `industry-agents` | `sequential` | 3 | 3 | 2 | 107 | ✅ Pass |
| `instagram_post` | `sequential` | 5 | 6 | 3 | 152 | ✅ Pass |
| `job-posting` | `sequential` | 3 | 5 | 3 | 125 | ✅ Pass |
| `landing_page_generator` | `sequential` | 4 | 7 | 8 | 143 | ✅ Pass |
| `markdown_validator` | `sequential` | 1 | 1 | 1 | 84 | ❌ Fail |
| `marketing_strategy` | `sequential` | 3 | 5 | 2 | 126 | ✅ Pass |
| `match_profile_to_positions` | `sequential` | 2 | 2 | 3 | 103 | ✅ Pass |
| `meta_quest_knowledge` | `sequential` | 1 | 1 | 0 | 82 | ✅ Pass |
| `prep-for-a-meeting` | `sequential` | 4 | 4 | 1 | 120 | ❌ Fail |
| `recruitment` | `sequential` | 4 | 4 | 3 | 129 | ❌ Fail |
| `screenplay_writer` | `sequential` | 5 | 5 | 0 | 139 | ✅ Pass |
| `starter_template` | `sequential` | 2 | 2 | 1 | 100 | ✅ Pass |
| `stock_analysis` | `sequential` | 4 | 4 | 8 | 134 | ❌ Fail |
| `surprise_trip` | `sequential` | 3 | 3 | 3 | 116 | ✅ Pass |
| `trip_planner` | `sequential` | 3 | 3 | 3 | 107 | ✅ Pass |

## Compilation Failure Logs

### CrewAI Scenario `markdown_validator` failure:
```python
  File "output_files/output_crewai/markdown_validator/crew.py", line 18
    - Tool na
           ^
SyntaxError: invalid syntax

```

### CrewAI Scenario `prep-for-a-meeting` failure:
```python
  File "output_files/output_crewai/prep-for-a-meeting/crew.py", line 18
    Provides three m
             ^
SyntaxError: invalid syntax

```

### CrewAI Scenario `recruitment` failure:
```python
  File "output_files/output_crewai/recruitment/crew.py", line 16
    tool_serperdev = SerperDevTool(name="SerperDevTool", name="Search API tool, configuration may include API key and search parameters (not included here).", note="SerperDevTool", note="Search API tool, configuration may include API key and search parameters (not included here).")
                                                         ^
SyntaxError: keyword argument repeated: name

```

### CrewAI Scenario `stock_analysis` failure:
```python
Sorry: IndentationError: unexpected indent (crew.py, line 20)
```

