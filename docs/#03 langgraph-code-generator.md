# Pipeline Analysis: LangGraph Code Generator Implementation

This document details the architecture and implementation of the **LangGraph Code Generator** (Task #03). This module is responsible for reading Knowledge Graph (KG) representations (`.ttl` files based on the Agent-O ontology) and translating them into executable Python code utilizing the LangGraph framework.

## 1. Module Architecture

The generator module is located in `src/langgraph/` and follows a decoupled, three-stage extraction and generation pipeline similar to the CrewAI implementation:

### A. Extractor (`src/langgraph/extractor.py`)
Responsible for parsing the RDF `.ttl` file using `rdflib`. It queries the graph for specific ontology classes and maps them to an **Intermediate Representation (IR)** (`models.py`).
* **Agents**: Queries `:LLMAgent` to extract roles, prompts, and model configurations (`:hasAgentConfig`).
* **Tools**: Queries `:Tool` to extract tool names and descriptions.
* **Nodes & Edges**: Queries `:WorkflowStep` and `:StartStep` to identify graph nodes, and traverses `:nextStep` relationships to map the execution flow.

### B. Generator (`src/langgraph/generator.py`)
Responsible for taking the Python IR objects and rendering them into executable code using **Jinja2 Templates**. 
Instead of hardcoding string concatenations, it uses pre-defined templates that enforce LangGraph best practices (e.g., proper `TypedDict` state definitions, `StateGraph` initializations, and `.compile()` mechanics).

### C. CLI Runner (`src/langgraph/run.py`)
The command-line interface that glues the Extractor and Generator together. It handles file I/O operations, ensuring the generated Python scripts are saved correctly into `output_files/output_langgraph/<project_name>/`.

## 2. Supported Agent Pattern Types

A core requirement for this generator is to support at least 3 distinct spatial arrangements (patterns) common in agentic workflows. The `LangGraphProject.pattern_type` property dynamically classifies the graph based on the loaded KG entities into one of the following templates:

### Pattern 1: Linear / Simple Chat Agent
* **Trigger condition**: 1 Agent, 0 Tools.
* **Description**: A basic sequential execution. The graph consists of a standard start edge pointing to a single LLM node, which then points to the end.
* **Demonstrated by**: `chat-agent_instances.ttl`

### Pattern 2: Tool-Calling Agent
* **Trigger condition**: 1 Agent, >= 1 Tools.
* **Description**: Incorporates functional augmentation. The generator maps tools via the `@tool` decorator, binds them to the LLM (`llm.bind_tools`), and builds a graph that shifts between the agent node and a standard `ToolNode` using LangGraph's native `tools_condition`.
* **Demonstrated by**: `open-code_instances.ttl`

### Pattern 3: Multi-Agent / Supervisor
* **Trigger condition**: > 1 Agents.
* **Description**: A hierarchical or routing pattern. A central supervisor node evaluates the state and decides which worker agent node should execute next. The generator writes conditional edges (`add_conditional_edges`) to handle dynamic routing between the supervisor and the workers.
* **Demonstrated by**: `supervisor_instances.ttl`

## 3. Usage & Execution

To generate code from an existing KG instance:

```bash
# General syntax
python src/langgraph/run.py <path_to_ttl_file>

# Example: Generating the Tool-Calling pattern
python src/langgraph/run.py generated_kg/LangGraph/open-code_instances.ttl
```

The system will output a ready-to-run project directory under `output_files/output_langgraph/<project_name>/` containing:
1. `main.py`: The executable LangGraph python script.
2. `requirements.txt`: The required pip dependencies (e.g., `langgraph`, `langchain-openai`).

To execute the final generated script:
```bash
cd output_files/output_langgraph/<project_name>
pip install -r requirements.txt
python main.py
```