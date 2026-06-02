FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONPATH=/app

# gcc/g++ are required to build wheels for numpy/pandas on slim images.
# git is required by pip for some VCS-resolved deps.
# curl is used by docker HEALTHCHECK.
# All in one layer to keep the image lean (no extra apt cache layer).
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        gcc g++ git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy ONLY manifests first so `pip install` is a cached layer
# that does not invalidate on every source-code edit.
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

COPY src/        ./src/
COPY scripts/    ./scripts/
COPY Script/     ./Script/
COPY agentO.ttl  ./agentO.ttl
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

LABEL org.opencontainers.image.title="agentic-generator" \
      org.opencontainers.image.description="Knowledge-graph-driven generator for Agentic AI frameworks (CrewAI / LangGraph / AutoGen)" \
      org.opencontainers.image.source="https://github.com/Software-Engineering-2026-Class/kelompok3-agentic-generator-paper"

ENTRYPOINT ["entrypoint.sh"]
CMD ["full"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app'); import src.crewai, src.langgraph; print('ok')" \
    || exit 1
