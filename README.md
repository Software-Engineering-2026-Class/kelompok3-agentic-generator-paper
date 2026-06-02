# Agentic AI Framework Generator

## Members
- Kenji Ratanaputra (24/534421/PA/22664) — [@Kenzi-GIT](https://github.com/Kenzi-GIT)
- Ayasha Rahmadinni (24/545462/PA/23178) — [@ayashar](https://github.com/ayashar)
- Kevin Antonio Wiyono Lauw (24/535917/PA/22736) — [@KevinAntonioWiyonoLauw](https://github.com/KevinAntonioWiyonoLauw)
- Melinda Annastasia Budijono (24/542840/PA/23052) — [@melinda-ab](https://github.com/melinda-ab)

## Project Links
- Repository: [Software-Engineering-2026-Class/kelompok3-agentic-generator-paper](https://github.com/Software-Engineering-2026-Class/kelompok3-agentic-generator-paper.git)
- GitHub Project: https://github.com/Software-Engineering-2026-Class/kelompok3-agentic-generator-paper
- Ontology reference: [Agentic AI Ontology](https://w3id.org/agentic-ai/onto)

## Description

This project is a knowledge-graph-driven generator for Agentic AI frameworks. It reads RDF/Turtle Knowledge Graphs built with the [Agentic AI Ontology](https://w3id.org/agentic-ai/onto), extracts the semantic structure of agents, tasks, tools, prompts, and workflows, and turns that structure into executable code for frameworks such as CrewAI and AutoGen.

### Project Overview

The generator bridges the gap between abstract agentic AI patterns defined in ontologies and concrete implementations in popular agentic AI frameworks. The repository also includes the scripts, templates, and generated Knowledge Graph instances needed to inspect, normalize, and reproduce the pipeline end to end.

### Key Features

- **Ontology-based Generation**: Uses the standard Agentic AI Ontology (https://w3id.org/agentic-ai/onto) as the foundation
- **Multi-framework Support**: Generates code for multiple agentic AI frameworks:
  - CrewAI
  - AutoGen
- **Knowledge Graph Parsing**: Reads and interprets KGs in RDF/Turtle format (.ttl, .rdf)
- **Pattern Recognition**: Extracts agentic AI patterns including agents, tasks, tools, and workflows
- **Automated Code Generation**: Produces executable Python scripts for target frameworks

### Documentation and Source Notes

- `Script/analysis.prompt.md` contains the ontology-population prompt used to turn source code and configuration into Turtle instances.
- `Script/run_prompt.py` is the main script that loads the ontology, reads source files, calls the model, and writes the generated `.ttl` output.
- `scripts/normalize_kg.py` normalizes generated Knowledge Graph files into the canonical agent pattern used by the repository.
- `scripts/add_kickoff_inputs.py` adds kickoff input bundles to generated TTL files.
- `generated_kg/` stores the generated Knowledge Graph instances for AutoGen, CrewAI, LangGraph, and Mastra AI.
- `output_files/` contains generated framework outputs and example code artifacts.

## License

This project is developed for academic and research purposes.  
The project references the Agentic AI Ontology (AgentO), which is distributed under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.

The source code of this repository is distributed under the MIT License.

### Initial Code

The main starting points for the codebase are:

- `Script/run_prompt.py` for the ontology-to-instance generation flow.
- `scripts/normalize_kg.py` for KG cleanup and canonicalization.
- `src/crewai/generator.py` for CrewAI code generation.
- `src/crewai/templates/main.py.j2` for the generated CrewAI entry point template.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nauraranantya/agentic-generator.git
   cd agentic-generator
   ```
2.	Create and activate a virtual environment:
   ```bash
  python -m venv venv
  source venv/bin/activate       # macOS/Linux
  venv\Scripts\activate          # Windows
  ```
3. Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

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

### Option 1: Generate Multi-Agent Code from Knowledge Graph
1. Place the Knowledge Graph (in .ttl or .rdf format) inside the data/ folder, or use the existing dummy data in `data/` or `kg_g3/`.
   Example: `data/dummy_kg.ttl`

2. Run the automated pipeline:
   ```bash
   python runner.py
   ```
   This will automatically:
   - Parse the knowledge graph ontology
   - Generate CrewAI framework code
   - Generate AutoGen framework code

3. Check the `output/` folder for generated scripts:
   - `crewai_generated.py`
   - `autogen_generated.py`

### Option 2: Test Workflow Simulation (Demo)
1. Place your gpt-4o-mini API key in a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

2. Run the pre-configured workflow test:
   ```bash
   python test_email_workflow.py
   ```
   This demonstrates a complete email auto-responder workflow using CrewAI with:
   - Email classification
   - Automated response generation
   - Quality review process

   OR
   
   ```bash
   python test_cust_support_workflow.py
   ```
   This demonstrates a customer support ticket handling workflow using AutoGen with:
   - Ticket classification and prioritization
   - Multi-agent collaboration for resolution
   - Automated response generation
3. View the complete workflow execution and results in the console output.