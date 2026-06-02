#!/usr/bin/env bash
# Entrypoint for the agentic-generator image.
# Dispatches to a pipeline stage based on the first argument.
# Usage:  entrypoint.sh <stage>
# Stages: full | normalize | crewai | langgraph | validate | stats |
#         evaluate | kickoff | prompt | bash | help

set -euo pipefail

cd /app

RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YLW=$'\033[1;33m'; CYN=$'\033[0;36m'; NC=$'\033[0m'
log()  { printf "${CYN}==>%s${NC}\n" "$*"; }
ok()   { printf "${GRN} [OK]${NC} %s\n" "$*"; }
warn() { printf "${YLW} [WARN]${NC} %s\n" "$*" >&2; }
err()  { printf "${RED} [ERR]${NC} %s\n" "$*" >&2; }

require_openai_key() {
  if [[ -z "${OPENAI_API_KEY:-}" || "${OPENAI_API_KEY:-}" == "your_api_key_here" ]]; then
    warn "OPENAI_API_KEY is not set or is a placeholder."
    warn "This stage may fail or produce incomplete output without a real key."
  fi
}

stage_normalize() {
  log "Stage 1/5 — Normalize Knowledge Graphs (generated_kg/CrewAI/*.ttl)"
  python scripts/normalize_kg.py
  ok "Normalization complete"
}

stage_kickoff() {
  log "Appending kickoff input bundles to CrewAI TTLs"
  python scripts/add_kickoff_inputs.py
  ok "Kickoff inputs appended"
}

stage_crewai() {
  log "Stage 2/5 — Generate CrewAI projects from KGs"
  python -m src.crewai.run
  ok "CrewAI generation complete"
}

stage_langgraph() {
  log "Stage 3/5 — Generate LangGraph projects from KGs"
  for ttl in generated_kg/LangGraph/*.ttl; do
    [[ -f "$ttl" ]] || continue
    log "  -> $(basename "$ttl")"
    python -m src.langgraph.run "$ttl" || warn "Failed on $ttl"
  done
  ok "LangGraph generation complete"
}

stage_validate() {
  log "Stage 4/5 — Validate generated LangGraph code"
  python scripts/validate_langgraph.py
  ok "Validation complete"
}

stage_stats() {
  log "Stage 5/5 — Generate framework statistics"
  python scripts/generate_statistics.py
  ok "Statistics generated"
}

stage_evaluate() {
  log "Running quality evaluation (offline, no OpenAI calls)"
  python scripts/evaluate_quality.py
  ok "Quality evaluation complete"
}

stage_prompt() {
  require_openai_key
  log "LLM ontology-population (uses OPENAI_API_KEY, processes ../crews/* by default)"
  if [[ $# -ge 2 ]]; then
    python Script/run_prompt.py "$2"
  else
    bash Script/run_all.sh
  fi
  ok "Prompt run complete"
}

stage_full() {
  printf "${GRN}============================================================${NC}\n"
  printf "${GRN}  Agentic AI Framework Generator — Full Pipeline${NC}\n"
  printf "${GRN}============================================================${NC}\n"

  stage_normalize
  stage_kickoff
  stage_crewai
  stage_langgraph
  stage_validate
  stage_stats

  printf "\n${GRN}============================================================${NC}\n"
  printf "${GRN}  Pipeline finished. Outputs in: /app/output_files/${NC}\n"
  printf "${GRN}============================================================${NC}\n"
}

usage() {
  cat <<EOF
Usage: entrypoint.sh <stage> [args]

Stages:
  full       Run the entire pipeline (normalize -> generate -> validate -> stats)
  normalize  Normalize generated_kg/CrewAI/*.ttl to canonical agent pattern
  kickoff    Append kickoff input bundles to CrewAI TTLs
  crewai     Generate CrewAI projects from generated_kg/CrewAI
  langgraph  Generate LangGraph projects from generated_kg/LangGraph
  validate   Run syntax/structural/runtime validation on generated code
  stats      Generate summary statistics across generated frameworks
  evaluate   Run quality evaluation (offline, no API calls)
  prompt     LLM ontology-population (requires OPENAI_API_KEY) [folder]
  bash       Drop into an interactive shell
  help       Show this help

Examples:
  docker compose up app
  docker compose run --rm app normalize
  docker compose run --rm app prompt ./some_folder
EOF
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  full)      stage_full ;;
  normalize) stage_normalize ;;
  kickoff)   stage_kickoff ;;
  crewai)    stage_crewai ;;
  langgraph) stage_langgraph ;;
  validate)  stage_validate ;;
  stats)     stage_stats ;;
  evaluate)  stage_evaluate ;;
  prompt)    stage_prompt "$@" ;;
  bash|shell) exec /bin/bash ;;
  help|-h|--help) usage ;;
  *) err "Unknown stage: $cmd"; usage; exit 1 ;;
esac
