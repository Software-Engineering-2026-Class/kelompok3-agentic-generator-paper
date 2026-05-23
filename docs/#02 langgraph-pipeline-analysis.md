# Pipeline Analysis: LangGraph Mapping to Agent-O Ontology

This document provides an analysis of how **LangGraph** framework abstractions (Agents, Tasks, Tools, and Workflows) are identified and mapped to the existing Knowledge Graph pattern (`agentO.ttl`) in the extraction pipeline.

## 1. Abstraction Identification & Mapping

LangGraph uses a unique graph-based state machine approach to define agent workflows. It focuses heavily on `StateGraph`, `Nodes`, `Edges`, and `State`. Here is how these abstractions map to the `agentO.ttl` ontology.

### ✅ Supported Patterns (Direct Mapping)

The following LangGraph abstractions are successfully mapped and interpreted into the Knowledge Graph:

| LangGraph Abstraction | Ontology Pattern (`agentO.ttl`) | Description & Implementation |
| :--- | :--- | :--- |
| **StateGraph (Whole workflow)** | `:WorkflowPattern` | Evaluated as the main container of the system's workflow logic. Often grouped inside a `:Team` to bind agents to the pattern. |
| **Node (Process / Graph Node)** | `:WorkflowStep` / `:Task` | Function nodes in the graph translate to Workflow Steps. The semantic behavior of that node (e.g., calling an LLM or running a tool) maps to a `:Task` performed by an `:LLMAgent`. |
| **Edge (Standard Transition)** | `:nextStep` | A standard, direct edge from Node A to Node B is mapped using the `nextStep` property on the origin `WorkflowStep`. |
| **START Node** | `:StartStep` | The entry point edge in LangGraph (`START`) is represented by typing the specific node as a `:StartStep` with `:stepOrder 1`. |
| **Model / Agent Execution** | `:LLMAgent` | Nodes interacting with LLMs (e.g., `ChatOpenAI`) are characterized as `:LLMAgent`. Runtime configs (like `model="gpt-4o-mini"`) map to `:Config` via `:hasAgentConfig`. |
| **Graph State (e.g., MessagesAnnotation)** | `:KnowledgeBase` / `:Resource` | LangGraph passes a typed state dict (like `messages`) through nodes. This is encoded as a Knowledge Base or expected Resource required/produced by a task, though strictly tracked via prompt descriptions. |
| **Tools** | `:Tool` | Functions bound to LLMs (`bind_tools()`) are recognized as `:Tool` instances with basic attributes like `dcterms:title` and general `:hasCapability`. |

## 2. ❌ Unsupported / Ignored Patterns

Due to the rigid semantic structure of RDF/Turtle and the dynamic programming paradigms inherently present in LangGraph, the following abstractions lack first-class representation in `agentO.ttl` and are either ignored or transformed into hardcoded strings (descriptions):

* **Conditional Edges (Routing Logic)**:
  LangGraph heavily uses conditional edges (`add_conditional_edges()`) where pure Python logic dictates the next node based on the current state. The ontology cannot represent this programmatic branching well, so conditions are bypassed or reduced to human-readable strings inside `dcterms:description`.
* **Zod Schemas / Strict Typing**:
  LangGraph frequently utilizes `zod` schemas or `TypedDict` for structured outputs and tool parameters. The ontology lacks constructs to formally map field-by-field typing. Schemas are merged into the LLM's `:taskPrompt` text or tool description as raw literals.
* **SDK compilation & UI Mechanics (`.compile()`)**:
  Execution engine details, async processing, UI component streams (like tool call chunks returning to frontends), or methods like `.compile()` are entirely ignored because the KG dictates *semantic behavior*, not framework runtime details.
* **Nested Configuration**:
  LangGraph lets users pass deeply nested config objects (e.g., `RunnableConfig`). The ontology only supports flat key-value strings (`:configKey`, `:configValue`), avoiding nested structural retention.

## 3. Summary of Extracted Instances

When running the extraction pipeline over a LangGraph application (e.g., `chat-agent` or `trip-planner`), the extraction will generate files like `generated_kg/LangGraph/chat-agent_instances.ttl`. 

Dalam skema ini, fokus utama grafik diterjemahkan menjadi **urutan semantik**. Meskipun kehilangan kemampuan percabangan dinamis (*conditional routing*) tingkat kode di KG, aliran kerja secara logis (StateGraph -> Node -> Task -> LLMAgent) tetap bisa divisualisasikan menggunakan kelas-kelas dasar Agent-O.