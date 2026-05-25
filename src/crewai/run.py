"""
CLI Runner: batch-process generated_kg/CrewAI/*.ttl → CrewAI project directories.

Pipeline: KG (.ttl) → SPARQL (Layer 1) → Pydantic IR (Layer 2) → YAML + Python (Layer 3)

Usage:
    From project root:
        python -m src.crewai.run

    Single file:
        python -m src.crewai.run path/to/file.ttl

    Or directly:
        python src/crewai/run.py
"""

import os
import sys
import shutil
import json
from datetime import datetime, timezone

# Support both `python -m` and direct script execution
try:
    from .extractor import extract_crew_project
    from .generator import generate_project
except ImportError:
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    )
    from src.crewai.extractor import extract_crew_project
    from src.crewai.generator import generate_project


def process_single(kg_path: str, output_dir: str) -> str:
    """
    Process a single TTL file through the 3-layer pipeline.

    Args:
        kg_path:    Path to the input .ttl file
        output_dir: Directory to write the generated project

    Returns:
        The output directory path
    """
    # Layer 1: SPARQL extraction → Layer 2: Pydantic IR
    project = extract_crew_project(kg_path)

    # Layer 3: File generation (YAML + Jinja2)
    res_dir = generate_project(project, output_dir)
    
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
        "framework": "crewai",
        "pattern": os.path.basename(output_dir),
        "generated_files": sorted(generated_files),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    with open(os.path.join(output_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    return res_dir


def main():
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    output_base = os.path.join(project_root, "output_files", "crewai")

    # ── Handle single-file mode ──
    if len(sys.argv) > 1 and sys.argv[1].endswith(".ttl"):
        kg_path = os.path.abspath(sys.argv[1])
        base_name = os.path.splitext(os.path.basename(kg_path))[0]
        # Remove _instances suffix for cleaner directory name
        dir_name = base_name.replace("_instances", "")
        output_dir = os.path.join(output_base, dir_name)

        print(f"[Processing] {kg_path}")
        process_single(kg_path, output_dir)
        print(f"[Done] → {output_dir}")
        return

    # ── Batch mode: process all TTL files ──
    kg_dir = os.path.join(project_root, "generated_kg", "CrewAI")

    if not os.path.isdir(kg_dir):
        print(f"[ERROR] KG directory not found: {kg_dir}")
        sys.exit(1)

    ttl_files = sorted(f for f in os.listdir(kg_dir) if f.endswith(".ttl"))
    if not ttl_files:
        print(f"[WARNING] No .ttl files found in {kg_dir}")
        sys.exit(0)

    # Clean output directory
    if os.path.exists(output_base):
        shutil.rmtree(output_base)
    os.makedirs(output_base, exist_ok=True)

    # Header
    print("=" * 65)
    print("  KG → SPARQL → Pydantic → CrewAI Project Generator")
    print("  Pipeline: 3-Layer Conversion (SPARQL / Pydantic / YAML+Jinja2)")
    print("=" * 65)
    print(f"  Source : {kg_dir}")
    print(f"  Output : {output_base}")
    print(f"  Files  : {len(ttl_files)} knowledge graphs")
    print("=" * 65)

    # Process each KG
    success = 0
    errors = []

    for filename in ttl_files:
        kg_path = os.path.join(kg_dir, filename)
        base_name = os.path.splitext(filename)[0]
        dir_name = base_name.replace("_instances", "")
        output_dir = os.path.join(output_base, dir_name)

        print(f"\n[Processing] {filename}")
        try:
            process_single(kg_path, output_dir)
            success += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
            errors.append((filename, str(e)))

    # Summary
    print("\n" + "=" * 65)
    print(f"  Done. {success}/{len(ttl_files)} projects generated successfully.")
    if errors:
        print(f"  Errors ({len(errors)}):")
        for fname, err in errors:
            print(f"    - {fname}: {err}")
    print("=" * 65)


if __name__ == "__main__":
    main()
