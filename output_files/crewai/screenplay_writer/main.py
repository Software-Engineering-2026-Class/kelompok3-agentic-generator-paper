"""
Auto-generated CrewAI Main: AICrewforscreenwriting

Source  : AgentO Knowledge Graph → SPARQL → Pydantic → Jinja2
Pipeline: 3-Layer Conversion Pipeline
"""

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load .env from this directory BEFORE importing crew (which triggers crewai init)
_HERE = Path(__file__).parent
load_dotenv(_HERE / ".env")

from crew import AICrewforscreenwriting


def _load_inputs() -> dict:
    """Load kickoff inputs from config/inputs.yaml.

    When a key maps to a list, the **first** item is used as the
    runtime value.  Reorder or edit the list in the YAML file to
    choose a different example.  Every value is cast to ``str``
    so that CrewAI template interpolation works consistently.
    """
    inputs_path = _HERE / "config" / "inputs.yaml"
    if not inputs_path.exists():
        return {}
    with open(inputs_path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not data:
        return {}
    result = {}
    for k, v in data.items():
        if isinstance(v, list) and v:
            result[k] = str(v[0])
        else:
            result[k] = str(v) if v is not None else ""
    return result


def run():
    """Run the AICrewforscreenwriting."""
    inputs = _load_inputs()
    AICrewforscreenwriting().crew().kickoff(inputs=inputs)


def train():
    """Train the AICrewforscreenwriting for a given number of iterations."""
    inputs = _load_inputs()
    try:
        AICrewforscreenwriting().crew().train(
            n_iterations=int(sys.argv[1]),
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


if __name__ == "__main__":
    result = run()
    print(result)
