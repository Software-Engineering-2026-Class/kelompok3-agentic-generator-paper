import os
import sys
import json
from datetime import datetime, timezone

try:
    from .extractor import extract_langgraph_project
    from .generator import generate_project
except ImportError:
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    )
    from src.langgraph.extractor import extract_langgraph_project
    from src.langgraph.generator import generate_project


def process_single(kg_path: str, output_dir: str) -> str:
    """
    Process a single TTL file into a LangGraph project.
    """
    print(f"Reading KG from {kg_path}...")
    project = extract_langgraph_project(kg_path)
    
    print(f"Detected LangGraph Pattern: {project.pattern_type}")
    print(f"- Extracted {len(project.agents)} Agent(s)")
    print(f"- Extracted {len(project.tools)} Tool(s)")
    print(f"- Extracted {len(project.nodes)} Node(s)")
    
    print(f"Generating Python code into {output_dir}...")
    generate_project(project, output_dir)
    print("Done!")
    
    # Generate Manifest
    generated_files = []
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file == "manifest.json":
                continue
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, output_dir)
            generated_files.append(rel_path.replace("\\", "/"))
            
    manifest = {
        "framework": "langgraph",
        "pattern": os.path.basename(output_dir),
        "generated_files": sorted(generated_files),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    with open(os.path.join(output_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    return output_dir

if __name__ == "__main__":
    if len(sys.argv) > 1:
        kg_path = sys.argv[1]
    else:
        kg_path = os.path.join("generated_kg", "LangGraph", "chat-agent_instances.ttl")
        
    raw_name = os.path.basename(kg_path).replace(".ttl", "").replace("_instances", "")
    out_dir = os.path.join("output_files", "langgraph", raw_name)
    
    process_single(kg_path, out_dir)