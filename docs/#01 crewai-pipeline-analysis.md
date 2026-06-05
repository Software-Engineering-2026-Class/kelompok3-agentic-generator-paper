# Pipeline Analysis: Agentic Generator for CrewAI

This document provides an end-to-end analysis of the CrewAI generation pipeline. It covers the pipeline architecture, supported Knowledge Graph (KG) patterns mapped from `agentO.ttl`, and expected input/output formats.

## 1. Pipeline Overview

The project features a **two-way (reverse and forward) engineering pipeline** that bridges CrewAI Python code and an Ontology-based Knowledge Graph (`agentO.ttl`).

### Part A: Reverse Engineering (Extraction Pipeline)
**Script**: `Script/run_prompt.py`

This script parses existing CrewAI source code and pushes it to an LLM (OpenAI) to extract its semantic structure.

* **Expected Input**: 
  A folder containing the source code of an existing AI Agent framework (e.g., `src/crewai/` or a project folder containing Python and `.env` files).
* **Expected Output**: 
  A structured RDF Turtle (`.ttl`) file adhering to the `agento:` namespace (e.g., `generated_kg/CrewAI/gym_planner_instances.ttl`).

### Part B: Forward Engineering (Generation Pipeline)
**Script**: `src/crewai/run.py` (which leverages `extractor.py` and `generator.py`)

This pipeline reads the generated `.ttl` files and reconstructs a fully runnable CrewAI Python project.

* **Expected Input**:
  A `.ttl` file containing instance data based on `agentO.ttl`.
* **Expected Output**:
  A ready-to-run Python project directory (usually placed in `output_files/crewai/<project_name>/`), which typically includes:
  * `crew.py`: Defines the Crew, Agents, and Tasks logic.
  * `main.py`: The execution entry point (`kickoff` script).
  * `.env`: Environment variables and API keys (if defined in the KG).
  * `config/` (Optional depending on setup): YAML configurations.

## 2. Supported Knowledge Graph (KG) Patterns

Based on the mapping between `agentO.ttl` and the Python generator (`src/crewai/extractor.py`), the following patterns define the capabilities and limitations of the current generation pipeline.

### ✅ Supported Patterns
The following components are successfully parsed from the KG and generated into Python Code:

| Pattern / Entity | Ontology Properties Used | Generated CrewAI Output |
| :--- | :--- | :--- |
| **Team (Crew)** | `:Team`, `dcterms:title`, `:hasAgentMember` | Creates the main `@crew` class in `crew.py`. Links instances of agents. |
| **LLM Agents** | `:LLMAgent`, `:agentRole`, `dcterms:description`, `:agentPrompt` (Backstory), `:hasAgentGoal` | Generates `@agent` decorators. Maps backstories, roles, and goals directly into the `Agent` class parameters. |
| **Tasks** | `:Task`, `dcterms:description`, `:taskPrompt` (Expected Output), `:performedByAgent` | Generates `@task` decorators and maps the expected output and assigned agent into the `Task` configuration. |
| **Tools (Basic)** | `:Tool`, `:hasCapability`, `dcterms:title` | Assigns capabilities to tools mapped to agents. |
| **Workflow Seq.** | `:StartStep`, `:EndStep`, `:nextStep` | Configures the execution process type (e.g., `Process.sequential`) inside the Crew configuration. |

### ❌ Unsupported / Ignored Patterns
The following properties exist in the ontology but are either ignored by the generator, not natively supported by CrewAI, or require manual Python adjustment:

* **Direct Agent Interaction (`:interactsWith`)**: 
  The ontology allows defining direct agent-to-agent communication links. Currently, the generator ignores this and relies entirely on CrewAI's default sequential task handoffs.
* **Resource Artifacts (`:producedResource`, `:requiresResource`)**:
  While the ontology captures Input/Output artifacts as `Resource` nodes (e.g., `CitySelectionReportResource`), the code generator does not map these into CrewAI's `output_file` or `output_json` properties explicitly yet.
* **Complex Tooling logic**:
  Detailed python imports (like mapping specific Langchain Tools) are not fully abstracted in the KG and often require manual intervention post-generation.

## 3. How to Run the Pipeline (End-to-End)

1. **Extraction (Code to KG):**
   ```bash
   # From root directory
   python Script/run_prompt.py <path_to_existing_crewai_project>
   ```
   *Result: A new `.ttl` file in `agent-o/` directory.*

2. **Generation (KG to Code):**
   ```bash
   # Ensure environment is active
   python src/crewai/run.py generated_kg/CrewAI/<your_instance>.ttl
   ```
   *Result: A generated python project in `output_files/crewai/`.*

3. **Execution (Run the generated code):**
   ```bash
   cd output_files/crewai/<generated_project_name>
   python main.py
   ```
