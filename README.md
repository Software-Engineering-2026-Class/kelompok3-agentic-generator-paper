# Agentic AI Framework Generator 🚀

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Frameworks](https://img.shields.io/badge/Target%20Frameworks-CrewAI%20%7C%20LangGraph%20%7C%20AutoGen-green.svg)](#)

A semantic-web-driven code generator that bridges the gap between formal ontology designs and operational multi-agent python applications. By reading RDF/Turtle Knowledge Graphs built with the **Agentic AI Ontology (AgentO)**, this generator parses semantic agentic configurations (agents, tasks, workflows, tools, and prompts) and automatically builds production-ready executable codebases for **CrewAI** and **LangGraph**.

This project supports **Two-Way Engineering**:
*   **Forward Engineering**: Knowledge Graph (`.ttl`) ──> SPARQL extraction ──> Pydantic IR ──> Jinja2 Python/YAML codebase.
*   **Reverse Engineering**: Source code / configuration ──> LLM parsing ──> RDF Turtle instance generation.

---

## 👥 Members (Kelompok 3 - Rekayasa Perangkat Lunak 2026)

*   **Kenji Ratanaputra** (24/534421/PA/22664) — [@Kenzi-GIT](https://github.com/Kenzi-GIT)
*   **Ayasha Rahmadinni** (24/545462/PA/23178) — [@ayashar](https://github.com/ayashar)
*   **Kevin Antonio Wiyono Lauw** (24/535917/PA/22736) — [@KevinAntonioWiyonoLauw](https://github.com/KevinAntonioWiyonoLauw)
*   **Melinda Annastasia Budijono** (24/542840/PA/23052) — [@melinda-ab](https://github.com/melinda-ab)

---

## 🌟 Key Features

*   **Ontology-Driven Generation**: Seamless mapping from [AgentO (Agentic AI Ontology)](https://w3id.org/agentic-ai/onto) to object models.
*   **Multi-Framework Architectures**:
    *   **CrewAI**: Outputs complete packages matching best practices (YAML-based dynamic agents/tasks, custom tools, dynamic kickoffs, `.env.example`, and manifest files).
    *   **LangGraph**: Outputs stateful multi-agent workflows matching **Linear**, **Tool-Calling**, and **Supervisor** orchestration patterns.
*   **AST-based Static Code Validation**: Validates generated code syntax offline (`py_compile`) and matches AST nodes against source Knowledge Graph specifications.
*   **Mock-based Dynamic Execution**: Simulates runtime execution of compiled graphs using mock LLMs (`MockChatOpenAI`) to ensure code runs flawlessly without requiring live OpenAI API keys or quotas.
*   **Comprehensive Codebase Coverage**: Processes batch/single input Turtle graphs, generating individual code projects inside `output_files/`.

---

## 📁 Workspace Structure

Below is the directory hierarchy of this repository:

```text
.
├── .venv/                      # Python virtual environment (ignored by git)
├── Script/                     # Reverse Engineering modules (Code -> TTL)
│   ├── analysis.prompt.md      # Structured LLM prompt template for populating ontology
│   ├── run_all.sh              # Bash script to batch-process target folders
│   └── run_prompt.py           # CLI calling OpenAI model to write instances
├── docs/                       # Reports, statistics & analytical docs
│   ├── quality_findings.md     # Quality bug analysis & root causes (e.g. IRI leaks, unnamed tools)
│   ├── quality_report.md       # Tabular score sheet for LangGraph quality evaluation
│   └── summary_statistics.md   # Generated code metrics & lines of code (LOC) statistics
├── generated_kg/               # Semantic Input Dataset (RDF Turtle instances)
│   ├── AutoGen/                # Autogen-derived instances
│   ├── CrewAI/                 # CrewAI-derived instances (17 scenarios)
│   ├── LangGraph/              # LangGraph-derived instances (9 scenarios)
│   └── Mastra AI/              # Mastra-derived instances
├── output_files/               # Target output for generated codebases (git-ignored)
│   ├── crewai/                 # Dynamically generated CrewAI code directories
│   └── langgraph/              # Dynamically generated LangGraph code directories
├── scripts/                    # Quality assurance & validation scripts
│   ├── add_kickoff_inputs.py   # Prepends input parameter templates to Turtle files
│   ├── evaluate_quality.py     # 3-stage QA pipeline (Syntax -> AST -> Mock execution)
│   ├── generate_statistics.py  # Generates LOC reports & counts target files
│   ├── normalize_kg.py         # Cleans and standardizes Turtle graph syntax
│   └── validate_langgraph.py   # Offline test execution of compiled graphs
├── src/                        # Core Engine (TTL -> Code)
│   ├── crewai/                 # CrewAI code generator modules
│   │   ├── extractor.py        # SPARQL queries & RDFLib parsing
│   │   ├── generator.py        # Jinja2 rendering & YAML builders
│   │   ├── models.py           # Pydantic data schemas representing CrewAI
│   │   └── run.py              # CLI batch/single processing runner
│   └── langgraph/              # LangGraph code generator modules
│       ├── extractor.py        # SPARQL queries & RDFLib parsing
│       ├── generator.py        # Logic builder for LangGraph patterns
│       ├── models.py           # Pydantic data schemas representing LangGraph
│       └── run.py              # CLI batch/single processing runner
├── ARCHITECTURE_MAP.md         # Markdown document illustrating system data flows
├── REPOSITORY_GUIDE.md         # Indonesian onboarding documentation for new developers
├── agentO.ttl                  # Base Agentic AI Ontology schema
├── pyproject.toml              # Build dependencies & metadata (uv compatible)
└── requirements.txt            # Dependency definitions for standard pip setups
```

---

## 🛠️ Tech Stack & Dependencies

*   **Language**: Python `3.10` to `3.13`
*   **Graph Manipulation**: `rdflib>=7.0.0` (SPARQL & Turtle graph parsing)
*   **Schema & Data Validation**: `pydantic>=2.0.0`
*   **Template Rendering**: `Jinja2` (Cleaner file rendering, preventing inline f-string templates)
*   **Static Code Analysis**: Native `ast` & `py_compile`
*   **Target AI Frameworks**: `crewai>=0.152.0`, `langgraph>=0.1.0`, `langchain-core`

---

## 🚀 Installation & Setup

## Quick Start with Docker

A complete containerized environment is provided. The whole pipeline (normalize → generate → validate → statistics) is runnable with a single command:

```bash
docker compose up
```

This builds the image on first run and executes the full pipeline. Output appears in `./output_files/`.

### Common commands

| Command | Purpose |
|---|---|
| `docker compose up` | Run the entire pipeline (normalize → generate → validate → stats) |
| `docker compose run --rm app normalize` | Run only the KG-normalization stage |
| `docker compose run --rm app crewai` | Generate only CrewAI projects |
| `docker compose run --rm app langgraph` | Generate only LangGraph projects |
| `docker compose run --rm app stats` | Generate only framework statistics |
| `docker compose run --rm app bash` | Open an interactive shell inside the image |
| `docker compose --profile pipeline up` | Run each stage as its own container (with `depends_on` ordering) |
| `docker compose --profile llm up` | Also run the optional LLM ontology-population stage (requires `OPENAI_API_KEY`) |
| `docker compose down --rmi local` | Stop and remove containers + the built image |

### Environment variables

Copy `.env.example` to `.env` and fill in your `OPENAI_API_KEY`. The default pipeline does **not** call the OpenAI API; only the `prompt` service (LLM ontology-population) does. A `.env` is therefore only required if you enable the `llm` profile.

### Pipeline stages

| Stage | Service (profile `pipeline`) | Container-only (`app`) |
|---|---|---|
| 1. Normalize KGs | `normalize` | `entrypoint.sh normalize` |
| 2. Append kickoff inputs | `kickoff` | `entrypoint.sh kickoff` |
| 3. Generate CrewAI | `generate-crewai` | `entrypoint.sh crewai` |
| 4. Generate LangGraph | `generate-langgraph` | `entrypoint.sh langgraph` |
| 5. Validate | `validate` | `entrypoint.sh validate` |
| 6. Statistics | `stats` | `entrypoint.sh stats` |

The multi-container `pipeline` profile runs each stage in a separate container with `depends_on: condition: service_completed_successfully` ordering, so stages run in sequence and the command exits only when the last one finishes.

## Usage
### 1. Prerequisites
Ensure you have Python installed (`>= 3.10`). Check your version:
```bash
python --version
```

### 2. Clone the Repository
```bash
git clone https://github.com/Software-Engineering-2026-Class/kelompok3-agentic-generator-paper.git
cd kelompok3-agentic-generator-paper
```

### 3. Create & Activate Virtual Environment
*   **Windows**:
    ```powershell
    python -m venv .venv
    .venv\Scripts\activate
    ```
*   **macOS/Linux**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Optionally, if you are developing or running the LangGraph tests, install standard execution requirements:)*
```bash
pip install langchain-openai langgraph langchain-core pydantic
```

---

## 📖 Usage Documentation

The generator features CLI runners for both forward engineering pathways.

### 1. Forward Engineering (KG ──> Code)

#### Generating CrewAI Projects
Processes all Turtle files in `generated_kg/CrewAI/` and generates complete CrewAI project folders under `output_files/crewai/`:
```bash
python src/crewai/run.py
```
To run a single file:
```bash
python src/crewai/run.py generated_kg/CrewAI/trip_planner_instances.ttl
```

#### Generating LangGraph Projects
Processes a Turtle file in `generated_kg/LangGraph/` and generates the corresponding Python orchestration file and requirements in `output_files/langgraph/`:
```bash
python src/langgraph/run.py generated_kg/LangGraph/chat-agent_instances.ttl
```

---

### 2. Quality Assurance & Evaluation (Offline)

You can run automated statistics and quality evaluation scripts to assess syntax validation, structure completeness, and execution correctness.

#### A. Generate Project Code Statistics
This script compiles the generated Python files, measures LOC, and counts files:
```bash
python scripts/generate_statistics.py
```
Outputs a markdown summary to `docs/summary_statistics.md`.

#### B. Evaluate Quality & Identify Errors (Issue #07)
Runs a 3-stage validation process (Syntax check ──> AST-vs-IR Comparison ──> Offline mock execution):
```bash
python scripts/evaluate_quality.py
```
This script runs **completely offline** (using a patched LLM mock system). It creates two critical documents under `docs/`:
1.  `docs/quality_report.md` - Tabular report showing quality scores for all LangGraph targets.
2.  `docs/quality_findings.md` - Diagnostic findings on namespace leaks, missing tools, and architectural pattern errors.

---

### 3. Reverse Engineering (Code ──> KG)

Extracts semantic structure from codebases into ontology instances.

```bash
# Ensure your OpenAI API key is exported:
# export OPENAI_API_KEY="your-api-key"

python Script/run_prompt.py path/to/source/code/folder
```

---

## 🐳 Docker Environment Setup (Upcoming Issue)

> [!NOTE]
> *This section is a placeholder for the upcoming Docker environment setup issue.*

A Docker environment will be introduced to containerize the generator pipeline. Once implemented, the workflow will proceed as follows:

### 1. Build the Docker Image
```bash
docker build -t agentic-generator:latest .
```

### 2. Run the Batch Pipeline Containerized
You can mount input KGs and generate code without polluting your local python environment:
```bash
docker run --rm \
  -v ${PWD}/generated_kg:/app/generated_kg \
  -v ${PWD}/output_files:/app/output_files \
  agentic-generator:latest python src/crewai/run.py
```

### 3. Running via Docker Compose
A `docker-compose.yml` configuration will support a clean development loop:
```yaml
version: '3.8'
services:
  generator:
    image: agentic-generator:latest
    volumes:
      - .:/app
    command: python src/langgraph/run.py generated_kg/LangGraph/chat-agent_instances.ttl
```
Execute with:
```bash
docker-compose up
```

---

## 📄 License

*   The ontology references the **Agentic AI Ontology (AgentO)** schema, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
*   The generator engine source code is distributed under the **MIT License**.