# Changelog

All notable changes to the **Agentic AI Framework Generator** project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-06-12

First complete release covering the full Kelompok 3 final-project scope: a
two-way (forward + reverse) ontology-driven generator targeting **CrewAI** and
**LangGraph**, a containerized pipeline, an offline quality-evaluation suite, and
full documentation.

### Added
- **Use cases documentation** — three reproducible end-to-end use cases (CrewAI generation, LangGraph tool-calling, offline quality evaluation) under `use-cases/`. (#09)
- **Docker environment** — `Dockerfile` (`python:3.12-slim`, layer-cached, healthcheck), `docker-compose.yml` with 7 services and 3 profiles (`pipeline`, `llm`, default), `entrypoint.sh` orchestrator with 9 stages, `.dockerignore`, and `.env.example`. Whole pipeline (normalize → generate → validate → stats) runs with `docker compose up`. (Infrastructure)
- **LangGraph code generator** — supports 3 orchestration patterns: **Linear**, **Tool-Calling**, and **Supervisor**. Emits `main.py`, `config/inputs.yaml`, `.env.example`, `requirements.txt`, and `manifest.json`. (#03)
- **Second-framework KG mapping** — mapped Agentic AI KG patterns to a second framework schema and extended the ontology with previously-missing properties. (#02, #08)
- **Offline quality evaluation** — `scripts/evaluate_quality.py` runs a 3-stage pipeline (syntax check → AST-vs-IR structural comparison → mock runtime) requiring no API key. Produces `docs/quality_report.md` and `docs/quality_findings.md` (average quality score 93.3/100). (#04, #07)
- **Summary statistics report** — `scripts/generate_statistics.py` outputs `docs/summary_statistics.md` with LOC counts and agent/task/tool tallies across frameworks. (#05)
- **Offline LangGraph validation** — `scripts/validate_langgraph.py` performs mock-runtime execution testing with a Mock LLM. (#04)
- **Output organization** — generated projects organized by framework/pattern, each with a `manifest.json` metadata file. (#06)
- **New KG instances & ontology properties** — additional Turtle instances and ontology properties to cover missing second-framework patterns. (#08)
- **Final project report** — complete technical report (BAB 1–6) with evaluation data and contribution table under `paper/`.
- **MIT License** and member roster in the README.

### Changed
- **README comprehensive rewrite** — merged the Docker pipeline section, expanded installation/usage docs, added the use-cases index, and resolved Issue #09. (#09)
- **Output structure** — refactored the generator to organize outputs per framework/pattern. (#06)

### Fixed
- **LangGraph execution** — resolved runtime execution issues in generated LangGraph projects. (#03)
- **Generator robustness** — fixed variable collisions, model parsing, and empty-agents exceptions in the LangGraph generator. (#07)
- **KG syntax** — fixed syntax errors in `utils_instances.ttl` and other LLM-generated Turtle files.
- **Dotenv loading** — generated projects load the local `.env` with `override=True` so per-project keys win over global environment variables.

---

## [0.2.0] - 2026-03-12 — Upstream baseline (pre-fork)

State of the upstream `raviearjun/agentic-generator-paper` project at the time of
the fork. Provided the CrewAI generation pipeline that Kelompok 3 audited and
built upon. (#01)

### Added
- CrewAI generation pipeline: extractor, modeler (Pydantic IR), and Jinja2/YAML generator.
- KG generation scripts, the AgentO ontology, and LangGraph / Mastra AI / AutoGen KG instances.
- Reverse-engineering prompt runner for code-to-KG extraction via LLM.

### Fixed
- Extractor logic, KG input fields, and ontology class/syntax flaws.
- Dotenv loading scoped to each `main.py` directory.
- OpenAI API key organization and generated-import cleanup.

---

## [0.1.0] - 2025-11-12 — Initial commit

### Added
- Initial Agentic AI KG parser and CrewAI & AutoGen mappers.
- First README and repository setup.

---

[1.0.0]: https://github.com/Software-Engineering-2026-Class/kelompok3-agentic-generator-paper/releases/tag/v1.0.0
[0.2.0]: https://github.com/Software-Engineering-2026-Class/kelompok3-agentic-generator-paper
[0.1.0]: https://github.com/Software-Engineering-2026-Class/kelompok3-agentic-generator-paper
