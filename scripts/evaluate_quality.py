"""
Issue #07 — Evaluate quality of generated LangGraph code.

Tiga tahap evaluasi (offline, tanpa API OpenAI):
  A. Syntax validation   (py_compile)
  B. Structural check    (AST vs IR comparison)
  C. Mock runtime test   (MockChatOpenAI)

Output: docs/quality_report.md  dan  docs/quality_findings.md
"""

import ast
import importlib.util
import logging
import os
import py_compile
import sys
import traceback
import warnings
from typing import Any
from unittest.mock import MagicMock

# Suppress rdflib serialization warnings (tidak relevan untuk evaluasi kualitas)
logging.getLogger("rdflib").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

# ── path setup ──────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.langgraph.extractor import extract_langgraph_project
from src.langgraph.models import LangGraphProject

# ── patch ChatOpenAI sebelum import apapun yang membutuhkannya ───────────────
import langchain_openai
from langchain_core.messages import AIMessage


class _MockLLM:
    """Drop-in pengganti ChatOpenAI untuk pengujian offline."""

    def __init__(self, *args, **kwargs):
        self.model = kwargs.get("model", "mock")

    def invoke(self, messages, *_a, **_kw):
        text = " ".join(
            m.content if hasattr(m, "content") else str(m)
            for m in (messages if isinstance(messages, list) else [])
        )
        # Supervisor pattern: kembalikan FINISH untuk mencegah infinite loop
        if any(kw in text.lower() for kw in ("supervisor", "decide who", "finish")):
            return AIMessage(content="FINISH")
        return AIMessage(content="Mocked LLM Response")

    def bind_tools(self, tools, *_a, **_kw):
        mock = MagicMock()
        mock.invoke.return_value = AIMessage(content="Tool response mocked")
        return mock


langchain_openai.ChatOpenAI = _MockLLM


# ── konstanta ────────────────────────────────────────────────────────────────
KG_DIR = os.path.join(PROJECT_ROOT, "generated_kg", "LangGraph")
OUT_DIR = os.path.join(PROJECT_ROOT, "output_files", "langgraph")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
WELL_KNOWN_NAMESPACE = "w3id.org/agentic-ai"


# ════════════════════════════════════════════════════════════════════════════
# TAHAP A — Syntax Validation
# ════════════════════════════════════════════════════════════════════════════

def check_syntax(main_py: str) -> tuple[bool, str]:
    """Kompilasi file Python. Kembalikan (ok, error_msg)."""
    if not os.path.exists(main_py):
        return False, "File main.py tidak ditemukan"
    try:
        py_compile.compile(main_py, doraise=True)
        return True, ""
    except py_compile.PyCompileError as exc:
        return False, str(exc)


# ════════════════════════════════════════════════════════════════════════════
# TAHAP B — Structural Check via AST + IR
# ════════════════════════════════════════════════════════════════════════════

def _collect_ast_info(source: str) -> dict[str, Any]:
    """Ekstrak informasi struktural dari source code Python menggunakan AST."""
    info: dict[str, Any] = {
        "tool_funcs": [],          # nama fungsi @tool
        "node_funcs": [],          # nama fungsi *_node
        "add_node_calls": [],      # argumen add_node(...)
        "has_stategraph": False,
        "has_app_compile": False,
        "system_message_contents": [],  # isi SystemMessage(content=...)
    }
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return info

    for node in ast.walk(tree):
        # Cari fungsi yang didekorasi @tool
        if isinstance(node, ast.FunctionDef):
            decorator_names = []
            for d in node.decorator_list:
                if isinstance(d, ast.Name):
                    decorator_names.append(d.id)
                elif isinstance(d, ast.Attribute):
                    decorator_names.append(d.attr)
            if "tool" in decorator_names:
                info["tool_funcs"].append(node.name)
            if node.name.endswith("_node"):
                info["node_funcs"].append(node.name)

        # Cari StateGraph(...)
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name == "StateGraph":
                info["has_stategraph"] = True
            # Cari workflow.add_node(...)
            if name == "add_node" and node.args:
                arg0 = node.args[0]
                if isinstance(arg0, ast.Constant):
                    info["add_node_calls"].append(arg0.value)
            # Cari workflow.compile()
            if name == "compile":
                info["has_app_compile"] = True
            # Cari SystemMessage(content=...)
            if name == "SystemMessage":
                for kw in node.keywords:
                    if kw.arg == "content":
                        if isinstance(kw.value, ast.Constant):
                            info["system_message_contents"].append(kw.value.value)
                        elif isinstance(kw.value, ast.JoinedStr):
                            info["system_message_contents"].append("<f-string>")
    return info


def _check_iri_leak(contents: list[str]) -> list[str]:
    """Kembalikan daftar content yang mengandung IRI namespace ontologi (bukan teks asli)."""
    leaked = []
    for c in contents:
        if WELL_KNOWN_NAMESPACE in c:
            leaked.append(c[:100] + "..." if len(c) > 100 else c)
    return leaked


def check_structure(ttl_path: str, main_py: str) -> dict[str, Any]:
    """Bandingkan IR dari TTL dengan AST dari main.py."""
    result: dict[str, Any] = {
        "ir_tools": [],
        "ir_agents": 0,
        "ir_pattern": "",
        "ast_tool_funcs": [],
        "ast_node_funcs": [],
        "ast_add_nodes": [],
        "has_stategraph": False,
        "has_compile": False,
        "tools_missing": [],
        "tools_unnamed": 0,
        "agents_found": 0,
        "pattern_match": False,
        "iri_leaked": [],
        "error": "",
    }

    # Ekstrak IR dari KG
    try:
        project: LangGraphProject = extract_langgraph_project(ttl_path)
    except Exception as exc:
        result["error"] = f"Gagal parsing TTL: {exc}"
        return result

    result["ir_tools"] = [t.var_name for t in project.tools]
    result["ir_agents"] = len(project.agents)
    result["ir_pattern"] = project.pattern_type

    # Baca dan parse source code
    if not os.path.exists(main_py):
        result["error"] = "main.py tidak ditemukan"
        return result

    source = open(main_py, encoding="utf-8").read()
    ast_info = _collect_ast_info(source)
    result["ast_tool_funcs"] = ast_info["tool_funcs"]
    result["ast_node_funcs"] = ast_info["node_funcs"]
    result["ast_add_nodes"] = ast_info["add_node_calls"]
    result["has_stategraph"] = ast_info["has_stategraph"]
    result["has_compile"] = ast_info["has_app_compile"]

    # Cek IRI leak di SystemMessage
    result["iri_leaked"] = _check_iri_leak(ast_info["system_message_contents"])

    # Bandingkan nama tool IR vs AST
    ir_tool_names = set(result["ir_tools"])
    ast_tool_names = set(result["ast_tool_funcs"])
    result["tools_unnamed"] = sum(1 for n in ast_tool_names if "unnamed" in n)
    result["tools_missing"] = list(ir_tool_names - ast_tool_names)

    # Bandingkan jumlah agent/node function
    result["agents_found"] = len(ast_info["node_funcs"])

    # Cek pattern match (heuristic sederhana berdasarkan template yang dipakai)
    if result["ir_pattern"] == "linear" and len(ast_tool_names) == 0:
        result["pattern_match"] = True
    elif result["ir_pattern"] in ("tool_calling", "supervisor") and len(ast_tool_names) > 0:
        result["pattern_match"] = True
    else:
        result["pattern_match"] = False

    return result


# ════════════════════════════════════════════════════════════════════════════
# TAHAP C — Mock Runtime Execution
# ════════════════════════════════════════════════════════════════════════════

def check_runtime(scenario: str, main_py: str) -> tuple[bool, str]:
    """Import dan eksekusi compiled LangGraph app dengan MockLLM."""
    if not os.path.exists(main_py):
        return False, "main.py tidak ditemukan"
    try:
        module_name = f"_lg_eval_{scenario}"
        spec = importlib.util.spec_from_file_location(module_name, main_py)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)

        if not hasattr(mod, "app"):
            return False, "Module tidak memiliki objek 'app' (compiled graph)"

        state = mod.app.invoke({"messages": [("user", "Hello, test the workflow.")]})
        msgs = state.get("messages", [])
        if not msgs:
            return False, "app.invoke() berhasil tapi 'messages' kosong"
        return True, ""
    except Exception:
        return False, traceback.format_exc().strip().split("\n")[-1]


# ════════════════════════════════════════════════════════════════════════════
# Hitung Quality Score
# ════════════════════════════════════════════════════════════════════════════

def compute_score(r: dict[str, Any]) -> float:
    """
    Weighted quality score (0-100) sesuai Implementation Plan Issue #07.

    Metrik dan Bobot:
      Syntax Correctness  20%  -- py_compile PASS?
      Tool Fidelity       20%  -- tools_missing / total (unnamed = warning saja, bukan error)
      Agent Completeness  20%  -- node functions vs expected agents
      Prompt Integrity    20%  -- tidak ada IRI bocor ke SystemMessage
      Pattern Accuracy    10%  -- detected pattern sesuai KG?
      Runtime Execution   10%  -- mock app.invoke() berhasil?
    """
    syntax_score = 20.0 if r["syntax_ok"] else 0.0

    # Tool Fidelity: hanya penalti jika tool benar-benar HILANG (missing).
    # Tools yang 'unnamed' tetap HADIR di kode — ini warning kualitas nama, bukan missing part.
    ir_count = len(r["ir_tools"])
    if ir_count == 0:
        tool_score = 20.0  # tidak ada tool di IR -> tidak ada yang bisa hilang
    else:
        missing_count = len(r["tools_missing"])
        tool_score = 20.0 * max(0, ir_count - missing_count) / ir_count

    # Agent Completeness: jumlah *_node function di AST vs jumlah agen di IR
    ir_agents = r["ir_agents"]
    if ir_agents == 0:
        agent_score = 20.0
    else:
        agent_score = 20.0 * min(r["agents_found"], ir_agents) / ir_agents

    # Prompt Integrity: IRI bocor -> prompt tidak terisikan dengan benar
    prompt_score = 0.0 if r["iri_leaked"] else 20.0

    # Pattern Accuracy & Runtime
    pattern_score = 10.0 if r["pattern_match"] else 0.0
    runtime_score = 10.0 if r["runtime_ok"] else 0.0

    total = syntax_score + tool_score + agent_score + prompt_score + pattern_score + runtime_score
    return round(total, 1)


# ════════════════════════════════════════════════════════════════════════════
# Evaluasi Satu Skenario
# ════════════════════════════════════════════════════════════════════════════

def evaluate_scenario(scenario: str) -> dict[str, Any]:
    """Jalankan 3 tahap evaluasi untuk satu skenario LangGraph."""
    ttl_path = os.path.join(KG_DIR, f"{scenario}_instances.ttl")
    main_py = os.path.join(OUT_DIR, scenario, "main.py")

    print(f"\n{'-'*55}")
    print(f"  Evaluasi: {scenario}")
    print(f"{'-'*55}")

    # Tahap A
    print("  [A] Syntax check ...", end=" ")
    syntax_ok, syntax_err = check_syntax(main_py)
    print("PASS" if syntax_ok else f"FAIL -- {syntax_err}")

    # Tahap B
    print("  [B] Structural check ...")
    struct = check_structure(ttl_path, main_py)
    if struct["error"]:
        print(f"      [WARN] {struct['error']}")

    _log_struct(struct)

    # Tahap C
    print("  [C] Mock runtime ...", end=" ")
    runtime_ok, runtime_err = check_runtime(scenario, main_py)
    print("PASS" if runtime_ok else f"FAIL -- {runtime_err}")

    result = {
        "scenario": scenario,
        "syntax_ok": syntax_ok,
        "syntax_error": syntax_err,
        **struct,
        "runtime_ok": runtime_ok,
        "runtime_error": runtime_err,
    }
    result["quality_score"] = compute_score(result)
    print(f"  [Score] {result['quality_score']}/100")
    return result


def _log_struct(s: dict) -> None:
    print(f"      IR tools ({len(s['ir_tools'])}): {s['ir_tools']}")
    print(f"      AST @tool fns ({len(s['ast_tool_funcs'])}): {s['ast_tool_funcs']}")
    if s["tools_missing"]:
        print(f"      [!] Missing tools: {s['tools_missing']}")
    if s["tools_unnamed"] > 0:
        print(f"      [!] Unnamed tools: {s['tools_unnamed']}")
    if s["iri_leaked"]:
        print(f"      [!] IRI leak di prompt: {len(s['iri_leaked'])} instance")
    print(f"      Pattern IR={s['ir_pattern']} | match={s['pattern_match']}")
    print(f"      StateGraph={s['has_stategraph']} | compile={s['has_compile']}")


# ════════════════════════════════════════════════════════════════════════════
# Generate Laporan Markdown
# ════════════════════════════════════════════════════════════════════════════

def _score_badge(score: float) -> str:
    if score >= 80:
        return f"🟢 {score}"
    if score >= 50:
        return f"🟡 {score}"
    return f"🔴 {score}"


def _bool_icon(val: bool) -> str:
    return "✅" if val else "❌"


def write_quality_report(results: list[dict]) -> str:
    """Tulis docs/quality_report.md dan kembalikan path-nya."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    path = os.path.join(DOCS_DIR, "quality_report.md")

    avg = sum(r["quality_score"] for r in results) / len(results) if results else 0

    lines = [
        "# Laporan Evaluasi Kualitas Kode LangGraph (Issue #07)",
        "",
        "> Evaluasi dilakukan **offline** tanpa kuota OpenAI menggunakan:",
        "> `py_compile` (syntax) · `ast` (struktur) · `MockChatOpenAI` (runtime)",
        "",
        f"**Total skenario:** {len(results)}  |  **Rata-rata quality score:** {avg:.1f}/100",
        "",
        "---",
        "",
        "## Ringkasan Hasil per Skenario",
        "",
        "| Skenario | Syntax | Tools IR→Kode | Agent Nodes | Prompt Bersih | Pattern | Runtime | **Score** |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for r in results:
        ir_t = len(r["ir_tools"])
        ast_t = len(r["ast_tool_funcs"])
        if r["tools_missing"]:
            tool_status = "MISS"
        elif r["tools_unnamed"] > 0:
            tool_status = "WARN"
        else:
            tool_status = "OK"
        tool_cell = f"{ast_t}/{ir_t} ({tool_status})"
        agent_cell = f"{r['agents_found']}/{r['ir_agents']} ({'OK' if r['agents_found']>=r['ir_agents'] else 'MISS'})"
        prompt_cell = "OK" if not r["iri_leaked"] else f"IRI ({len(r['iri_leaked'])})"
        lines.append(
            f"| `{r['scenario']}` "
            f"| {'OK' if r['syntax_ok'] else 'FAIL'} "
            f"| {tool_cell} "
            f"| {agent_cell} "
            f"| {prompt_cell} "
            f"| {'OK' if r['pattern_match'] else 'FAIL'} "
            f"| {'OK' if r['runtime_ok'] else 'FAIL'} "
            f"| **{r['quality_score']}/100** |"
        )

    lines += [
        "",
        "---",
        "",
        "## Detail Per-Skenario",
        "",
    ]

    for r in results:
        lines.append(f"### `{r['scenario']}` — Score {r['quality_score']}/100")
        lines.append("")
        lines.append(f"- **Pattern KG:** `{r['ir_pattern']}`")
        lines.append(f"- **Syntax:** {'PASS' if r['syntax_ok'] else 'FAIL — ' + r['syntax_error']}")
        lines.append(f"- **Tools di IR:** {r['ir_tools'] or 'tidak ada'}")
        lines.append(f"- **Tool functions di kode:** {r['ast_tool_funcs'] or 'tidak ada'}")
        if r["tools_missing"]:
            lines.append(f"- **⚠ Tool hilang:** {r['tools_missing']}")
        if r["tools_unnamed"] > 0:
            lines.append(f"- **⚠ Tool tanpa nama (unnamed):** {r['tools_unnamed']} fungsi")
        if r["iri_leaked"]:
            lines.append(f"- **❌ IRI bocor ke prompt:** {r['iri_leaked']}")
        lines.append(f"- **Pattern match:** {'Ya' if r['pattern_match'] else 'Tidak'}")
        lines.append(f"- **Runtime (mock):** {'PASS' if r['runtime_ok'] else 'FAIL — ' + r['runtime_error']}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def write_findings_report(results: list[dict]) -> str:
    """Tulis docs/quality_findings.md berdasarkan pola error yang ditemukan."""
    path = os.path.join(DOCS_DIR, "quality_findings.md")

    unnamed_scenarios = [r["scenario"] for r in results if r["tools_unnamed"] > 0]
    iri_scenarios = [r["scenario"] for r in results if r["iri_leaked"]]
    missing_scenarios = [r["scenario"] for r in results if r["tools_missing"]]
    pattern_fail = [r["scenario"] for r in results if not r["pattern_match"]]
    runtime_fail = [r["scenario"] for r in results if not r["runtime_ok"]]

    lines = [
        "# Temuan Root Cause — Issue #07",
        "",
        "Dokumen ini merangkum penyebab mendasar setiap kategori error kualitas yang ditemukan pada kode LangGraph yang di-generate.",
        "",
        "---",
        "",
        "## Finding 1 — Tool Names Hilang (`unnamed__tool`)",
        "",
        f"**Severity:** 🔴 Critical  |  **Skenario Terdampak:** {unnamed_scenarios or 'Tidak ada'}",
        "",
        "**Root Cause:**",
        "Extractor di `src/langgraph/extractor.py` (baris 38) mengambil nama tool hanya dari `dcterms:title`:",
        "```python",
        'title = str(g.value(tool_uri, dct.title) or "Unnamed Tool")',
        "```",
        "Namun banyak file TTL yang menggunakan `rdfs:label` sebagai nama tool (bukan `dcterms:title`).",
        "Akibatnya, nama tool tidak dapat ditemukan dan fallback ke `'Unnamed Tool'` → `unnamed__tool`.",
        "",
        "**Bukti:**",
        "```",
        ":Tool_stockbroker rdfs:label \"stockbroker\"  # di KG",
        "def unnamed__tool(...):  # di kode output",
        "```",
        "",
        "**Rekomendasi Perbaikan:**",
        "```python",
        "# Di extractor.py baris 38, ubah menjadi:",
        'rdfs = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")',
        'label = str(g.value(tool_uri, rdfs.label) or g.value(tool_uri, dct.title) or "Unnamed Tool")',
        "```",
        "",
        "---",
        "",
        "## Finding 2 — IRI Bocor ke Dalam Prompt (`agentPrompt` tidak di-resolve)",
        "",
        f"**Severity:** 🔴 Critical  |  **Skenario Terdampak:** {iri_scenarios or 'Tidak ada'}",
        "",
        "**Root Cause:**",
        "Extractor mengambil nilai `:agentPrompt` sebagai-is dari properti object:",
        "```python",
        'prompt = str(g.value(agent_uri, agento.agentPrompt) or "You are a helpful assistant.")',
        "```",
        "Tapi `:agentPrompt` adalah *object property* yang merujuk ke individu `:Prompt`,",
        "bukan literal teks. Sehingga yang tersimpan adalah IRI (URI) bukan isi promptnya.",
        "",
        "**Bukti:**",
        "```python",
        '# Di chat-agent/main.py:',
        'sys_msg = SystemMessage(content=\"\"\"http://www.w3id.org/agentic-ai/onto#ChatSystemPrompt\"\"\")',
        "```",
        "",
        "**Rekomendasi Perbaikan:**",
        "```python",
        "# Di extractor.py, resolve IRI ke teks :promptInstruction:",
        "prompt_uri = g.value(agent_uri, agento.agentPrompt)",
        "if prompt_uri:",
        "    prompt_text = str(g.value(prompt_uri, agento.promptInstruction) or",
        "                      g.value(prompt_uri, agento.promptContext) or",
        '                      "You are a helpful assistant.")',
        "else:",
        '    prompt_text = "You are a helpful assistant."',
        "```",
        "",
        "---",
        "",
        "## Finding 3 — Tool Spesifik Hilang dari Kode Output",
        "",
        f"**Severity:** 🟡 Medium  |  **Skenario Terdampak:** {missing_scenarios or 'Tidak ada'}",
        "",
        "**Root Cause:**",
        "Sebagian tool di KG terdaftar sebagai *agen* (tipe `:LLMAgent`) yang juga bertindak sebagai tool,",
        "bukan sebagai `:Tool` murni. Karena extractor menggunakan filter:",
        "```python",
        "FILTER NOT EXISTS { ?tool a :LLMAgent }  # di CrewAI extractor",
        "```",
        "Tool yang merupakan sub-agen ini tidak tertangkap.",
        "",
        "**Rekomendasi Perbaikan:**",
        "Tambahkan query fallback yang mengambil tool dari `agentToolUsage` langsung.",
        "",
        "---",
        "",
        "## Finding 4 — Pattern Detection Tidak Akurat",
        "",
        f"**Severity:** 🟡 Medium  |  **Skenario Terdampak:** {pattern_fail or 'Tidak ada'}",
        "",
        "**Root Cause:**",
        "Heuristik deteksi pattern di `src/langgraph/models.py` hanya berdasarkan jumlah agen:",
        "```python",
        "if len(self.agents) > 1:",
        '    return "supervisor"',
        "elif has_tools:",
        '    return "tool_calling"',
        "else:",
        '    return "linear"',
        "```",
        "Skenario `supervisor` yang sebenarnya hanya memiliki 1 `LLMAgent` utama,",
        "tapi workflow-nya adalah supervisor pattern. Deteksi berbasis jumlah agen tidak cukup.",
        "",
        "**Rekomendasi Perbaikan:**",
        "Tambahkan deteksi berbasis label/deskripsi WorkflowPattern atau adanya multiple WorkflowStep dengan tipe EndStep.",
        "",
        "---",
        "",
        "## Finding 5 — Runtime Failures",
        "",
        f"**Severity:** 🟡 Medium  |  **Skenario Terdampak:** {runtime_fail or 'Tidak ada'}",
        "",
        "Runtime gagal biasanya disebabkan oleh salah satu dari:",
        "1. Objek `app` tidak terbentuk karena error saat kompilasi graf.",
        "2. Node function menggunakan variabel yang tidak terdefinisi.",
        "3. Tool list kosong pada pola tool_calling.",
        "",
        "---",
        "",
        "## Ringkasan Prioritas Perbaikan",
        "",
        "| Prioritas | Finding | File yang Perlu Diubah |",
        "|---|---|---|",
        "| 🔴 P1 | Resolve agentPrompt IRI → teks | `src/langgraph/extractor.py` |",
        "| 🔴 P1 | Gunakan rdfs:label sebagai fallback nama tool | `src/langgraph/extractor.py` |",
        "| 🟡 P2 | Perbaiki pattern detection heuristik | `src/langgraph/models.py` |",
        "| 🟡 P2 | Tangkap sub-agent sebagai tool | `src/langgraph/extractor.py` |",
        "| 🟢 P3 | Tingkatkan mock test coverage | `scripts/validate_langgraph.py` |",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


# ════════════════════════════════════════════════════════════════════════════
# Entry point
# ════════════════════════════════════════════════════════════════════════════

def main():
    ttl_files = sorted(f for f in os.listdir(KG_DIR) if f.endswith(".ttl"))
    scenarios = [f.replace("_instances.ttl", "").replace(".ttl", "") for f in ttl_files]

    print("=" * 55)
    print("  Issue #07 - LangGraph Quality Evaluation")
    print("  Mode: OFFLINE (no API key required)")
    print("=" * 55)
    print(f"  Skenario ditemukan: {len(scenarios)}")

    results = []
    for sc in scenarios:
        r = evaluate_scenario(sc)
        results.append(r)

    # Ringkasan konsol
    print("\n" + "=" * 55)
    print("  RINGKASAN AKHIR")
    print("=" * 55)
    scores = [r["quality_score"] for r in results]
    avg = sum(scores) / len(scores) if scores else 0
    print(f"  Rata-rata Quality Score: {avg:.1f}/100")
    for r in results:
        tier = "[HIGH]" if r["quality_score"] >= 80 else ("[MED]" if r["quality_score"] >= 50 else "[LOW]")
        print(f"  {tier} {r['scenario']:<25} {r['quality_score']:>5}/100")

    # Tulis laporan
    rpt = write_quality_report(results)
    fnd = write_findings_report(results)
    print(f"\n  [OK] Laporan ditulis ke:")
    print(f"       {rpt}")
    print(f"       {fnd}")
    print("=" * 55)


if __name__ == "__main__":
    main()
