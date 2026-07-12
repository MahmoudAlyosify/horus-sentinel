# HORUS Sentinel — Agent Handoff & Run Guide

> **You are a coding agent (VS Code / Copilot / Cursor). This file is your complete brief.**
> Follow it top‑to‑bottom to get HORUS Sentinel running on this machine — first as a
> zero‑setup app, then fully containerized with Docker so it runs **anywhere, on any
> machine, with nothing pre‑installed but Docker**. Do exactly what each step says and
> verify each checkpoint before moving on. Do not refactor the app; your job is to run it.

---

## 0. What this project is (context)

HORUS Sentinel is an autonomous, multi‑agent **OSINT & threat‑intelligence platform**. A
swarm of passive agents gathers open‑source intelligence, correlates it into an
**Intelligence Knowledge Graph**, and a self‑hosted fine‑tuned LLM reasons over it to
produce prioritized, evidence‑backed **intelligence reports**. It is passive, auditable,
and human‑validated by design.

**Key architectural fact you must understand:** every heavy dependency is an *optional
accelerator* with a graceful fallback. The app runs fully **offline with zero infra**:

| Full stack (optional) | Fallback (always works) |
|---|---|
| PostgreSQL | SQLite file |
| Neo4j graph DB | in‑process `networkx` graph |
| ChromaDB vector RAG | deterministic keyword retriever |
| Ollama fine‑tuned model | deterministic grounded synthesis |
| LangGraph runtime | pure‑Python `Orchestrator` |
| Redis job queue | in‑memory `asyncio` queue |

So `docker compose up` (or even just `uvicorn`) yields a **working app immediately**.
Loading the fine‑tuned model is an enhancement, not a requirement.

---

## 1. CRITICAL: repository layout

The git repo root contains a **nested** project folder. **All commands run from the nested
project directory**, not the git root.

```
<repo-root>/                      # git root (has .git, the master plan .md)
└── horus-sentinel/               # <-- THE PROJECT. cd HERE. Everything below is relative to it.
    ├── api/  core/  agents/  tools/  graph/  scoring/  rag/  horus_brain/
    ├── workflows/  reporting/  schemas/
    ├── horus-ui/                 # self-contained Command Center (served at /ui)
    ├── data/                     # attack_knowledge.json + geo_corpus.sample.json
    ├── deploy/docker-compose.yml # the full stack
    ├── Dockerfile  requirements.txt  requirements-dev.txt
    ├── RUN.md  README.md  AGENT_HANDOFF.md (this file)
    └── horus-geointel/           # FROZEN placeholder — see §9. DO NOT modify or delete.
```

> If you cloned `git clone …/horus-sentinel.git`, the project is at
> `horus-sentinel/horus-sentinel/`. `cd` into that inner folder now.

Active branch: **`develop`**.

---

## 2. Prerequisites

- **Docker Desktop + Compose v2** (for the full stack). This is the only hard requirement.
- **Python 3.12** (3.13 also works) — only needed for the no‑Docker path (§5) and tests.
- Internet access for the first Docker build (downloads base images + Python wheels, ~1–2 GB).
- A GPU (this box has an RTX Ada 5000) — only needed to *serve the fine‑tuned model* (§4).

### 2.1 This machine is Windows 11 — read this

- Use **Docker Desktop for Windows** with the **WSL2** backend. `docker compose` commands
  work natively in **PowerShell**; the containers themselves run Linux inside WSL2, so the
  Linux image/Dockerfile are correct as‑is. Nothing about the app is Windows‑specific.
- **`curl` gotcha:** in PowerShell, `curl` is an alias for `Invoke-WebRequest` and does NOT
  accept `-s`/`-X`. Use **`curl.exe`** for the verify commands below, or use
  `Invoke-RestMethod` (examples given), or just use a browser for GET requests.
- **`make` is not built into Windows.** The optional `Makefile` shortcuts require **Git
  Bash** (or WSL). If you don’t have `make`, ignore it and use the explicit commands here —
  they are complete on their own.
- **Python venv activation (PowerShell):** `.venv\Scripts\Activate.ps1`
  (if blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).
- **GPU for the model:** the simplest route on Windows is the **native Ollama for Windows**
  app (installs the NVIDIA runtime, uses the RTX directly — no WSL GPU passthrough needed).
  See §4, Option A.

---

## 3. PRIMARY PATH — run the full app with Docker (do this first)

From the **project directory** (`horus-sentinel/horus-sentinel/`):

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

This builds the app image (from `Dockerfile`) and starts: **api**, **worker**, postgres,
neo4j, redis, chroma, minio, ollama. No `.env` is required — every value has a safe default.

### 3.1 Verify (must all pass)

> On **Windows PowerShell** use `curl.exe` (not `curl`) for the commands below, or the
> `Invoke-RestMethod` equivalents shown. On Git Bash / Linux, plain `curl` is fine.

```bash
# a) All containers up (api + worker + datastores)
docker compose -f deploy/docker-compose.yml ps

# b) Health endpoint returns ok
curl.exe -s http://localhost:8000/health
#    expect: {"status":"ok","service":"horus-sentinel",...}

# c) Command Center loads — open http://localhost:8000/ui in a browser
#    -> click "Run Guided Demo" -> you get a report card + a risk-colored graph

# d) Guided Demo via API (fully offline, deterministic)
curl.exe -s -X POST http://localhost:8000/demo
#    expect JSON: {"subject":"Sinai","status":"completed","entity_count":>0, "report_url":"/jobs/<id>/report", ...}

# e) Authorization gate refuses out-of-scope (this refusal is a FEATURE) -> expect 403
curl.exe -s -o NUL -w "%{http_code}\n" -X POST http://localhost:8000/jobs ^
  -H "Content-Type: application/json" ^
  -d "{\"subject\":{\"type\":\"domain\",\"value\":\"attacker.com\"},\"roe\":{\"subject\":\"attacker.com\",\"enabled_sources\":[\"web_infra\"],\"in_scope_domains\":[\"example.com\"],\"signed_by\":\"a\",\"expires_at\":\"2999-01-01T00:00:00\"}}"
```

**PowerShell‑native equivalents** (b, c/d, e):

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod -Method Post http://localhost:8000/demo        # -> status "completed"
try { Invoke-RestMethod -Method Post http://localhost:8000/jobs -ContentType application/json `
  -Body '{"subject":{"type":"domain","value":"attacker.com"},"roe":{"subject":"attacker.com","enabled_sources":["web_infra"],"in_scope_domains":["example.com"],"signed_by":"a","expires_at":"2999-01-01T00:00:00"}}' }
catch { $_.Exception.Response.StatusCode.value__ }   # expect 403
```

If (a)–(e) pass, **the application is running and portable.** You are essentially done —
§4 (model) is an optional quality upgrade.

### 3.1b Shortcuts (optional — if `make` is available)

A `Makefile` wraps the common commands. `make help` lists them. Examples:
`make up` (build + start stack), `make verify` (health + guided demo), `make logs`,
`make ps`, `make model-pull`, `make down`. Local dev: `make deps`, `make run`, `make check`
(lint + typecheck + tests). If `make` isn’t installed, use the explicit commands in this doc.

### 3.2 Logs / stop

```bash
docker compose -f deploy/docker-compose.yml logs -f api worker   # follow logs
docker compose -f deploy/docker-compose.yml down                 # stop (keeps volumes)
docker compose -f deploy/docker-compose.yml down -v              # stop + wipe data
```

### 3.3 Async workers (already wired)

A dedicated `worker` service consumes queued jobs and runs them **resumably** (it checkpoints
each stage; a killed job continues from where it stopped). Submit async work with:
`POST /jobs` → `POST /jobs/{id}/enqueue`. Scale workers:
`docker compose -f deploy/docker-compose.yml up -d --scale worker=3`.

---

## 4. OPTIONAL — serve the fine‑tuned model on the GPU (upgrades the brain)

Without this, the analysis narrative uses a deterministic *offline synthesis*. With it, the
fine‑tuned `Horus-OSINT` model narrates. Reports and the graph are identical in structure
either way (the model never invents facts).

### Option A — Native Ollama for Windows (RECOMMENDED on this Windows + RTX box)

Easiest GPU path on Windows 11 — no WSL passthrough needed.

1. Install **Ollama for Windows** from https://ollama.com/download (it sets up the NVIDIA
   runtime and serves on `http://localhost:11434`).
2. Load the model (PowerShell):
   ```powershell
   ollama pull hf.co/mahmoudalyosify/Horus-OSINT
   # or from a local file:  ollama create horus-osint -f deploy\Modelfile.example
   ollama list                      # should show horus-osint
   ```
3. Point the containers at the host’s Ollama. Create/edit `.env` in the project dir:
   ```
   OLLAMA_ENDPOINT=http://host.docker.internal:11434
   ```
   then `docker compose -f deploy/docker-compose.yml up -d` (recreates api/worker with the new endpoint).

### Option B — Ollama inside Docker (cross‑platform; needs WSL2 GPU for acceleration)

```bash
# Pull the model into the compose ollama service (service-based; works on any OS):
docker compose -f deploy/docker-compose.yml exec ollama ollama pull hf.co/mahmoudalyosify/Horus-OSINT

# From a local GGUF + the provided Modelfile:
docker compose -f deploy/docker-compose.yml cp ./Horus-OSINT.gguf ollama:/root/
docker compose -f deploy/docker-compose.yml exec ollama sh -c \
  'printf "FROM /root/Horus-OSINT.gguf\n" > /root/Modelfile && ollama create horus-osint -f /root/Modelfile'

docker compose -f deploy/docker-compose.yml exec ollama ollama list   # should list horus-osint
```

> For GPU **inside** the container on Windows, Docker Desktop must have WSL2 GPU support
> (NVIDIA driver + WSL2). Then add to the `ollama` service in `deploy/docker-compose.yml`:
> ```yaml
>     deploy:
>       resources:
>         reservations:
>           devices:
>             - driver: nvidia
>               count: all
>               capabilities: [gpu]
> ```
> If GPU passthrough is troublesome, prefer **Option A** (native Ollama).

After loading the model, run a fresh assessment from `/ui`; the report’s `generated_by`
field will show `horus-osint` instead of `offline-synthesis`.

---

## 5. ALTERNATIVE — run without Docker (laptop / quick check)

```bash
cd horus-sentinel/horus-sentinel        # the project dir
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -r requirements-dev.txt     # full deps (incl. test/lint tooling)

uvicorn api.main:app --reload
#   -> Command Center: http://localhost:8000/ui   (Guided Demo works offline)
#   -> API docs:       http://localhost:8000/docs
```

This uses SQLite + networkx + keyword‑RAG + offline synthesis automatically. Nothing else
to configure.

---

## 6. Verify the codebase (tests, lint, types)

```bash
cd horus-sentinel/horus-sentinel
pip install -r requirements-dev.txt     # if not already

pytest -q                               # ~85 tests, all offline (network mocked). Expect all pass (1 redis test skips if redis absent).
ruff check .                            # lint — expect "All checks passed!"
ruff format --check .                   # formatting — expect clean
mypy                                    # type check on core/tools/schemas — expect "no issues"
```

The GitHub Actions CI (`.github/workflows/ci.yml`) runs the same on every push.

---

## 7. API reference (what the UI and you can call)

| Method & path | Purpose |
|---|---|
| `GET /health` | Liveness probe |
| `GET /ui` | The Command Center (static SPA) |
| `POST /jobs` | Create + authorize a job `{subject, roe}` → **403 if out of scope** |
| `GET /jobs/{id}` | Job state (status, counts, validation) |
| `GET /jobs` | List recent jobs |
| `POST /jobs/{id}/run` | Run collection + reasoning synchronously (stops at validation) |
| `POST /jobs/{id}/enqueue` | Queue the job for a worker (async, resumable) |
| `GET /jobs/{id}/report` | The Report Card + Cytoscape graph JSON |
| `POST /jobs/{id}/validate` | Analyst action `{action: validate\|flag\|edit, analyst, note}` — a report is FINAL only after `validate`; a `validate` renders HTML+JSON+PDF |
| `GET /jobs/{id}/download/{fmt}` | Download the rendered report — `pdf` (real Arabic RTL) \| `html` \| `json` (renders on demand) |
| `POST /demo` | One‑click Guided Demo (offline, safe subject) → full report |
| `GET /setup/status` | First-run status: brain backend, HF token validity, per-transport reachability |
| `POST /setup/hf-token` | Save + validate the Hugging Face token `{token, backend?, model_id?, endpoint_url?}` (400 if rejected) |

Subject shapes: `{"type":"domain","value":"example.com"}` or
`{"type":"region","value":"Sinai","year_from":2018,"year_to":2019}`.

---

## 8. Configuration (env vars — all optional, sane defaults)

Copy `.env.example` → `.env` only if you want to override defaults. Key ones:

| Var | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./horus_sentinel.db` | Postgres URL on the full stack (compose sets it) |
| `QUEUE_BACKEND` | `memory` | `redis` on the full stack (compose sets it) |
| `RAG_BACKEND` | `keyword` | `chroma` for semantic RAG (opt‑in) |
| `OLLAMA_ENDPOINT` | `http://localhost:11434` | Fine‑tuned model server |
| `HORUS_MODEL_NAME` | `horus-osint` | Ollama model tag |
| `GEO_CORPUS_PATH` | `data/geo_corpus.json` | Real GTD/GDELT corpus; falls back to the bundled sample |
| `WORKER_ENABLED` | `false` | Run an in‑process worker on API startup (single‑node) |
| API keys (`SHODAN_API_KEY`, `VIRUSTOTAL_API_KEY`, `ABUSEIPDB_API_KEY`, …) | empty | Optional enrichment; tools skip gracefully without them |

---

## 9. IMPORTANT — the `horus-geointel/` folder (do not touch)

`horus-geointel/` is a **frozen placeholder** for the team’s award‑winning original project.
The maintainer will copy that original project into it separately. **You must NOT create,
fabricate, modify, or delete anything in `horus-geointel/`.** The HORUS Sentinel app does
**not** depend on it — everything runs without it. Leave it exactly as is.

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `docker compose` build fails on a Python wheel | Ensure internet; retry `up -d --build`. The image needs manylinux wheels for chromadb/langgraph/weasyprint. |
| App starts but `/demo` errors “no such table” | Only happens if the startup lifespan didn’t run. Use the documented `uvicorn api.main:app` (it runs `init_db()` on startup). In Docker this is automatic. |
| `generated_by: offline-synthesis` (wanted the model) | Ollama not reachable or model not loaded — do §4, confirm `ollama list` shows `horus-osint`. |
| PDF report not produced | WeasyPrint system libs missing. The Docker image bundles them; locally, HTML+JSON are still produced (PDF is skipped, non‑fatal). |
| Geo agent finds nothing | The sample corpus covers Sinai/Levant/Sahel/Cairo 2018–2019. Add rows to `data/geo_corpus.json` (a JSON with a `records` array) for more regions. |
| Neo4j browser empty | The MVP graph is in‑process; the Neo4j mirror is best‑effort. Ensure the `neo4j` service is up. Not required for the app to work. |
| Port already in use | Edit the `ports:` mappings in `deploy/docker-compose.yml`. |

---

## 11. Definition of Done (your acceptance criteria)

You are done when **all** of these hold:

1. `docker compose -f deploy/docker-compose.yml up -d --build` brings up every service; `ps` shows them healthy/started.
2. `curl http://localhost:8000/health` → `{"status":"ok",...}`.
3. Opening `http://localhost:8000/ui` and clicking **Run Guided Demo** produces a report card + a risk‑colored graph.
4. `POST /demo` returns `status: "completed"` with `entity_count > 0`.
5. The out‑of‑scope `POST /jobs` example returns **403**.
6. `pytest -q` is green (from the project dir, in a venv with `requirements-dev.txt`).
7. `horus-geointel/` is untouched.

When these pass, HORUS Sentinel is a portable application that runs on this machine and any
other machine with Docker — with no further setup. Report success and stop.

---

*HORUS Sentinel · ARGUS’s hundred eyes gather; the Eye of HORUS judges · passive · auditable · human‑validated.*
