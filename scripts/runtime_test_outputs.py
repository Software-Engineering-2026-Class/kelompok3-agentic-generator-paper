"""
Runtime execution validator for generated output projects.

This script performs real execution smoke tests (not syntax-only):
- LangGraph: imports generated main.py, compiles graph, invokes app.invoke(...)
- CrewAI: imports generated main.py, calls run(), and patches Crew.kickoff

Each project runs in an isolated subprocess with timeout so one failing project
cannot block the whole validation run.

Usage examples:
  python scripts/runtime_test_outputs.py
  python scripts/runtime_test_outputs.py --framework all
  python scripts/runtime_test_outputs.py --framework langgraph --project chat-agent
  python scripts/runtime_test_outputs.py --framework crewai --timeout 45
"""

from __future__ import annotations

import argparse
import importlib.util
import multiprocessing as mp
import os
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = PROJECT_ROOT / "output_files"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORT_PATH = DOCS_DIR / "runtime_execution_report.md"


@dataclass
class TestResult:
    framework: str
    project: str
    status: str
    details: str
    duration_sec: float


def _iter_project_dirs(base_dir: Path, selected_project: str | None = None) -> list[Path]:
    if not base_dir.exists():
        return []
    dirs = [p for p in base_dir.iterdir() if p.is_dir()]
    dirs.sort(key=lambda p: p.name)
    if selected_project:
        dirs = [p for p in dirs if p.name == selected_project]
    return dirs


def _import_module_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _langgraph_worker(project_dir: str, queue: mp.Queue):
    try:
        project_path = Path(project_dir)
        main_py = project_path / "main.py"
        if not main_py.exists():
            raise FileNotFoundError(f"main.py not found: {main_py}")

        # Ensure local imports (if any) resolve from generated project dir.
        sys.path.insert(0, str(project_path))

        # Patch ChatOpenAI to avoid external API dependency while still running graph.
        try:
            import langchain_openai
        except ModuleNotFoundError as exc:
            queue.put(("SKIP", f"Missing dependency: {exc}"))
            return

        from langchain_core.messages import AIMessage
        from unittest.mock import MagicMock

        class MockChatOpenAI:
            def __init__(self, *args, **kwargs):
                self.model = kwargs.get("model", "mock-model")

            def invoke(self, messages, *_a, **_kw):
                text = " ".join(
                    m.content if hasattr(m, "content") else str(m)
                    for m in (messages if isinstance(messages, list) else [])
                )
                # End supervisor flow quickly and avoid infinite loops.
                if any(x in text.lower() for x in ("supervisor", "decide who", "finish")):
                    return AIMessage(content="FINISH")
                return AIMessage(content="Mocked LLM Response")

            def bind_tools(self, tools, *_a, **_kw):
                runnable = MagicMock()
                runnable.invoke.return_value = AIMessage(content="Mocked tool response")
                return runnable

        langchain_openai.ChatOpenAI = MockChatOpenAI

        module_name = f"_runtime_lg_{project_path.name}_{os.getpid()}"
        module = _import_module_from_file(module_name, main_py)

        if not hasattr(module, "app"):
            raise AttributeError("Generated module has no compiled graph object 'app'")

        state = module.app.invoke({"messages": [("user", "Runtime execution smoke test")]} )
        msgs = state.get("messages", []) if isinstance(state, dict) else []
        if not msgs:
            raise RuntimeError("app.invoke() returned empty messages")

        queue.put(("PASS", f"Executed app.invoke successfully; messages={len(msgs)}"))
    except Exception:
        queue.put(("FAIL", traceback.format_exc().strip()))


def _crewai_worker(project_dir: str, queue: mp.Queue):
    try:
        project_path = Path(project_dir)
        main_py = project_path / "main.py"
        if not main_py.exists():
            raise FileNotFoundError(f"main.py not found: {main_py}")

        # Ensure imports like "from crew import ..." resolve.
        sys.path.insert(0, str(project_path))

        try:
            from crewai import Crew
        except ModuleNotFoundError as exc:
            queue.put(("SKIP", f"Missing dependency: {exc}"))
            return

        from unittest.mock import patch

        call_counter = {"kickoff": 0}

        def fake_kickoff(self, *args, **kwargs):
            call_counter["kickoff"] += 1
            return {"status": "mocked_kickoff_ok", "inputs_keys": sorted((kwargs.get("inputs") or {}).keys())}

        def fake_train(self, *args, **kwargs):
            return {"status": "mocked_train_ok"}

        with patch.object(Crew, "kickoff", fake_kickoff), patch.object(Crew, "train", fake_train):
            module_name = f"_runtime_crew_{project_path.name}_{os.getpid()}"
            module = _import_module_from_file(module_name, main_py)

            if not hasattr(module, "run"):
                raise AttributeError("Generated main.py has no run() function")

            module.run()

        if call_counter["kickoff"] == 0:
            raise RuntimeError("run() finished but Crew.kickoff was never called")

        queue.put(("PASS", "Executed run() successfully; Crew.kickoff was called"))
    except Exception:
        queue.put(("FAIL", traceback.format_exc().strip()))


def _run_with_timeout(worker: Callable[[str, mp.Queue], None], project_dir: Path, timeout_sec: int) -> tuple[str, str, float]:
    queue: mp.Queue = mp.Queue()
    proc = mp.Process(target=worker, args=(str(project_dir), queue), daemon=True)

    started = datetime.now(timezone.utc)
    proc.start()
    proc.join(timeout=timeout_sec)

    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=2)
        finished = datetime.now(timezone.utc)
        duration = (finished - started).total_seconds()
        return "FAIL", f"Timeout after {timeout_sec}s", duration

    finished = datetime.now(timezone.utc)
    duration = (finished - started).total_seconds()

    if not queue.empty():
        status, details = queue.get()
        if status not in {"PASS", "FAIL", "SKIP"}:
            status = "FAIL"
        return str(status), str(details), duration

    if proc.exitcode == 0:
        return "PASS", "Completed without details", duration
    return "FAIL", f"Process exited with code {proc.exitcode}", duration


def _run_framework(framework: str, base_dir: Path, worker: Callable[[str, mp.Queue], None], timeout_sec: int, selected_project: str | None) -> list[TestResult]:
    results: list[TestResult] = []
    projects = _iter_project_dirs(base_dir, selected_project)

    if not projects:
        if selected_project:
            results.append(
                TestResult(framework, selected_project, "FAIL", "Project directory not found", 0.0)
            )
        else:
            results.append(
                TestResult(framework, "-", "FAIL", f"No generated projects found in {base_dir}", 0.0)
            )
        return results

    for project_dir in projects:
        status, details, duration = _run_with_timeout(worker, project_dir, timeout_sec)
        results.append(
            TestResult(
                framework=framework,
                project=project_dir.name,
                status=status,
                details=details,
                duration_sec=round(duration, 2),
            )
        )
    return results


def _summarize(results: Iterable[TestResult]) -> tuple[int, int, int, int]:
    results_list = list(results)
    total = len(results_list)
    passed = sum(1 for r in results_list if r.status == "PASS")
    skipped = sum(1 for r in results_list if r.status == "SKIP")
    failed = total - passed - skipped
    return total, passed, failed, skipped


def _write_report(results: list[TestResult]) -> Path:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    total, passed, failed, skipped = _summarize(results)
    ts = datetime.now(timezone.utc).isoformat()

    lines = [
        "# Runtime Execution Report",
        "",
        "Validation mode: real runtime smoke-test for generated projects (not syntax-only).",
        "",
        f"- Timestamp (UTC): {ts}",
        f"- Total projects tested: {total}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Skipped: {skipped}",
        "",
        "## Results",
        "",
        "| Framework | Project | Status | Duration (s) | Details |",
        "|---|---|---|---:|---|",
    ]

    for r in results:
        details = r.details.replace("\n", "<br>").replace("|", "\\|")
        lines.append(f"| {r.framework} | {r.project} | {r.status} | {r.duration_sec:.2f} | {details} |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Runtime smoke-test for generated output files (LangGraph/CrewAI)."
    )
    parser.add_argument(
        "--framework",
        choices=["langgraph", "crewai", "all"],
        default="langgraph",
        help="Target framework to test (default: langgraph).",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="Optional single project directory name (e.g., chat-agent).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout per project in seconds (default: 30).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.timeout <= 0:
        print("[ERROR] --timeout must be > 0")
        return 2

    results: list[TestResult] = []

    if args.framework in ("langgraph", "all"):
        lg_results = _run_framework(
            framework="langgraph",
            base_dir=OUTPUT_ROOT / "langgraph",
            worker=_langgraph_worker,
            timeout_sec=args.timeout,
            selected_project=args.project,
        )
        results.extend(lg_results)

    if args.framework in ("crewai", "all"):
        crew_results = _run_framework(
            framework="crewai",
            base_dir=OUTPUT_ROOT / "crewai",
            worker=_crewai_worker,
            timeout_sec=args.timeout,
            selected_project=args.project,
        )
        results.extend(crew_results)

    total, passed, failed, skipped = _summarize(results)

    print("=" * 72)
    print("Runtime Execution Validation")
    print("=" * 72)
    print(f"Target framework : {args.framework}")
    print(f"Selected project : {args.project or 'ALL'}")
    print(f"Timeout/project  : {args.timeout}s")
    print("-" * 72)

    for r in results:
        print(f"[{r.status}] {r.framework}/{r.project} ({r.duration_sec:.2f}s)")
        if r.status == "FAIL":
            tail = r.details.splitlines()[-1] if r.details else "Unknown error"
            print(f"       reason: {tail}")
        if r.status == "SKIP":
            print(f"       skip: {r.details}")

    report_path = _write_report(results)

    print("-" * 72)
    print(f"Summary: total={total}, pass={passed}, fail={failed}, skip={skipped}")
    print(f"Report : {report_path}")
    print("=" * 72)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
