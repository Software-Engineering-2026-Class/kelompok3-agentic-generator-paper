import os
import sys
import importlib.util
import traceback
from unittest.mock import MagicMock

# Set up path to import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.langgraph.run import process_single
from langchain_core.messages import AIMessage
import langchain_openai

# Setup the global mock for ChatOpenAI
class MockChatOpenAI:
    def __init__(self, *args, **kwargs):
        self.model = kwargs.get("model", "mocked-model")
        print(f"    [Mock LLM] Initialized ChatOpenAI with model: '{self.model}'")
        
    def invoke(self, messages, *args, **kwargs):
        prompt_text = ""
        for m in messages:
            if hasattr(m, 'content'):
                prompt_text += m.content + " "
            elif isinstance(m, tuple) and len(m) > 1:
                prompt_text += m[1] + " "
        
        # Check if supervisor routing prompt
        if "Decide who goes next" in prompt_text or "supervisor" in prompt_text.lower():
            # Return FINISH to avoid infinite loops in multi-agent tests
            print("    [Mock LLM] Supervisor routing -> FINISH")
            return AIMessage(content="FINISH")
            
        print("    [Mock LLM] Standard invocation -> Mocked LLM Response")
        return AIMessage(content="Mocked LLM Response")
        
    def bind_tools(self, tools, *args, **kwargs):
        mock_runnable = MagicMock()
        # Returns AIMessage when invoked
        mock_runnable.invoke.return_value = AIMessage(content="Mocked response with tools")
        print(f"    [Mock LLM] Bound tools: {[getattr(t, 'name', str(t)) for t in tools]}")
        return mock_runnable

# Patch the langchain_openai.ChatOpenAI class
langchain_openai.ChatOpenAI = MockChatOpenAI

def main():
    kg_dir = os.path.join("generated_kg", "LangGraph")
    ttl_files = [f for f in os.listdir(kg_dir) if f.endswith(".ttl")]
    ttl_files.sort()
    
    print("=" * 60)
    print(f"Starting LangGraph Validation on {len(ttl_files)} TTL files...")
    print("=" * 60)
    
    results = {}
    
    for ttl in ttl_files:
        kg_path = os.path.join(kg_dir, ttl)
        raw_name = ttl.replace(".ttl", "").replace("_instances", "")
        out_dir = os.path.join("output_files", "langgraph", raw_name)
        
        print(f"\nProcessing {ttl}...")
        try:
            # Generate the Python code
            process_single(kg_path, out_dir)
            
            # Paths to verify
            main_py = os.path.join(out_dir, "main.py")
            if not os.path.exists(main_py):
                raise FileNotFoundError(f"Generated main.py not found at {main_py}")
                
            # Load and execute the compiled graph
            print(f"  Validating execution of {main_py}...")
            module_name = f"main_{raw_name}"
            spec = importlib.util.spec_from_file_location(module_name, main_py)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            if not hasattr(module, "app"):
                raise AttributeError("Generated module does not contain the compiled graph 'app'")
                
            # Invoke the graph
            print("  Invoking compiled graph 'app'...")
            state = module.app.invoke({"messages": [("user", "Hello! Let's test the workflow.")]})
            
            print(f"  Success! Graph executed successfully.")
            results[raw_name] = {
                "status": "success",
                "error": None
            }
        except Exception as e:
            err_msg = traceback.format_exc()
            print(f"  FAILED with error: {e}")
            results[raw_name] = {
                "status": "failed",
                "error": err_msg
            }
            
    # Print Summary Report
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY REPORT")
    print("=" * 60)
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    failed_count = sum(1 for r in results.values() if r["status"] == "failed")
    print(f"Total: {len(results)} | Success: {success_count} | Failed: {failed_count}\n")
    
    for name, res in results.items():
        status_str = "SUCCESS" if res["status"] == "success" else "FAILED"
        print(f"- {name:<25} : {status_str}")
        if res["status"] == "failed":
            print(f"  Error details:\n{res['error']}")
            
    # Write report to markdown
    report_path = os.path.join("docs", "validation_results.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# LangGraph Execution Validation Report\n\n")
        f.write(f"Conducted offline validation using a mocked LLM environment. Since OpenAI API quota is exhausted, this report documents the correctness of compilation, schemas, and framework execution under offline simulation.\n\n")
        f.write("## Execution Summary\n\n")
        f.write(f"- **Total Patterns Tested**: {len(results)}\n")
        f.write(f"- **Passed**: {success_count}\n")
        f.write(f"- **Failed**: {failed_count}\n\n")
        
        f.write("## Detailed Results\n\n")
        f.write("| Pattern Name | Status | Error / Context |\n")
        f.write("| --- | --- | --- |\n")
        for name, res in results.items():
            status_emoji = "✅ SUCCESS" if res["status"] == "success" else "❌ FAILED"
            err_snippet = "None"
            if res["status"] == "failed":
                err_lines = res["error"].strip().split("\n")
                err_snippet = f"<pre>{err_lines[-1]}</pre>"
            f.write(f"| `{name}` | {status_emoji} | {err_snippet} |\n")
            
        if failed_count > 0:
            f.write("\n## Failure Details\n\n")
            for name, res in results.items():
                if res["status"] == "failed":
                    f.write(f"### `{name}` Failure Stack\n")
                    f.write(f"```python\n{res['error']}\n```\n\n")
                    
    print(f"\nWritten detailed validation report to: {report_path}")

if __name__ == "__main__":
    main()
