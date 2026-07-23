# HORUS Sentinel — Claude Code guide

Autonomous, **passive** multi-agent OSINT / threat-intelligence platform (ITC-Egypt 2026).
Specialized agents collect public intel, ground it in a knowledge graph + RAG, and a
self-hosted HORUS brain authors evidence-backed reports. Humans validate before anything is final.

## Repo layout

- **Git root (this folder):** docs, pitch materials, and this `CLAUDE.md`.
- **Application package:** `horus-sentinel/` — FastAPI API, agents, tools, graph, RAG, `horus_brain/`, UI, tests, deploy.

When running or testing application code, `cd horus-sentinel` first.

## Commands (from `horus-sentinel/`)

```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements-dev.txt
uvicorn api.main:app --reload                    # UI http://localhost:8000/ui
pytest                                           # offline-friendly suite
ruff check . && ruff format --check .
```

Full stack (optional): `docker compose -f deploy/docker-compose.yml up -d` from `horus-sentinel/`.

## Conventions

- Prefer existing patterns in `agents/`, `api/`, `horus_brain/`, `core/`, `tools/`.
- Keep changes small and focused; match local style (ruff).
- Brain transports today: HF / Ollama / offline synthesis via `horus_brain/brain.py`. Do not swap the product brain to Claude API unless explicitly requested as an app feature.
- Optional services degrade gracefully; prefer code that works offline when possible.

## Safety / do not

- Platform is **passive and defensive**. Do not add unauthorized active recon, exploitation, or attacks on third-party infrastructure. See `horus-sentinel/RESPONSIBLE_USE.md`.
- Never commit secrets: `.env`, API keys, tokens, credentials.
- **`horus-sentinel/horus-geointel/` is FROZEN** — do not modify, fabricate, or delete it. Build around it.
