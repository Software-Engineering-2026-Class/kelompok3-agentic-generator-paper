# UC-3 — Evaluate Generated Code Quality Offline (No API Key)

## Summary

| Field | Value |
|-------|-------|
| **Actor** | QA engineer / Researcher validating generator output |
| **Goal** | Score the quality and correctness of every generated LangGraph project without spending OpenAI quota |
| **Direction** | Quality Assurance (post-generation) |
| **Framework** | LangGraph |
| **Precondition** | LangGraph projects already generated under `output_files/langgraph/`; no API key required |
| **Trigger** | QA engineer runs the offline evaluation script |

## Description

After generating code (UC-1, UC-2), the team needs evidence that the output is
correct and faithful to the source Knowledge Graph. Because the OpenAI quota is
exhausted and CI must run without secrets, the evaluator runs **fully offline** using
a 3-stage pipeline:

1. **[A] Syntax check** — `py_compile` confirms each `main.py` is valid Python.
2. **[B] Structural check (AST vs IR)** — `ast` parses the generated file and compares
   its `@tool` functions and detected pattern against the Pydantic IR extracted from
   the KG. It also flags **IRI leaks** (raw ontology URIs in prompts) and **unnamed
   tools**.
3. **[C] Mock runtime** — a `MockChatOpenAI` stand-in executes the compiled graph to
   confirm it runs end-to-end without a real LLM.

Each scenario is scored out of 100; deductions apply for IRI leaks and unnamed tools.

## Input

**Command:**
```bash
python scripts/evaluate_quality.py
```

**Source data:** all 9 generated LangGraph projects in `output_files/langgraph/`
(`chat-agent`, `email-agent`, `open-code`, `pizza-orderer`, `stockbroker`,
`supervisor`, `trip-planner`, `utils`, `writer-agent`).

## Output

**Console output (excerpt):**
```
=======================================================
  Issue #07 - LangGraph Quality Evaluation
  Mode: OFFLINE (no API key required)
=======================================================
  Skenario ditemukan: 9

-------------------------------------------------------
  Evaluasi: trip-planner
-------------------------------------------------------
  [A] Syntax check ... PASS
  [B] Structural check ...
      IR tools (4): ['extract', 'classify', 'list_accommodations', 'list_restaurants']
      AST @tool fns (4): ['extract', 'classify', 'list_accommodations', 'list_restaurants']
      Pattern IR=tool_calling | match=True
  [C] Mock runtime ... PASS
  [Score] 100.0/100

=======================================================
  RINGKASAN AKHIR
=======================================================
  Rata-rata Quality Score: 93.3/100
```

**Generated reports:**
- `docs/quality_report.md` — per-scenario score table + root-cause detail
- `docs/quality_findings.md` — analysis of IRI leaks, unnamed tools, pattern misdetection

**Representative result table (`docs/quality_report.md`):**

| Scenario | Syntax | Pattern | Runtime | Score |
|----------|:------:|:-------:|:-------:|:-----:|
| `chat-agent` | OK | linear | OK | 80.0/100 |
| `email-agent` | OK | tool_calling | OK | 100.0/100 |
| `open-code` | OK | tool_calling | OK | 100.0/100 |
| `pizza-orderer` | OK | tool_calling | OK | 80.0/100 |
| `stockbroker` | OK | tool_calling | OK | 80.0/100 |
| `supervisor` | OK | tool_calling | OK | 100.0/100 |
| `trip-planner` | OK | tool_calling | OK | 100.0/100 |
| `utils` | OK | tool_calling | OK | 100.0/100 |
| `writer-agent` | OK | tool_calling | OK | 100.0/100 |

## Result / Postcondition

- **9/9** scenarios pass syntax, structural, and mock-runtime checks
  (`docs/validation_results.md`).
- **Average quality score: 93.3/100.**
- Lower-scoring scenarios are explained: the 80/100 cases (`chat-agent`,
  `pizza-orderer`, `stockbroker`) each lose points because a raw ontology IRI leaked
  into the system prompt (e.g. `...onto#ChatSystemPrompt`) — a concrete, actionable
  finding for the next iteration rather than a silent failure.

## Notes & Limitations

- The evaluation is intentionally **deterministic and offline**; it validates
  structural fidelity and compilation, not the semantic quality of real LLM responses.
- Related QA commands:
  ```bash
  python scripts/generate_statistics.py   # LOC / agent / task / tool tallies → docs/summary_statistics.md
  python scripts/validate_langgraph.py     # mock-runtime execution only
  ```
