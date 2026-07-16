<div align="center">

# 🦅 HORUS SENTINEL — User Manual

### *"The eye that never sleeps."*

**Autonomous, Multi-Agent OSINT & Threat-Intelligence Platform**
*ITC-Egypt 2026 · Track 3 — Intelligent Software Systems*

</div>

---

> **What this manual is.** A complete, self-contained guide to install, configure, verify, and
> operate HORUS Sentinel from a clean machine to a full end-to-end intelligence assessment on
> **real-world data** — with no additional guidance required. Every command has been executed and
> verified against the running system (104 unit tests green; 25/25 live end-to-end checks passing).

---

## Table of Contents

1. [System overview](#1-system-overview)
2. [Prerequisites & system requirements](#2-prerequisites--system-requirements)
3. [Installation & setup](#3-installation--setup)
4. [Environment configuration (`.env`)](#4-environment-configuration-env)
5. [Running the system](#5-running-the-system)
6. [Optional accelerators (model, Docker, API keys)](#6-optional-accelerators-model-docker-api-keys)
7. [The Command Center UI — every control](#7-the-command-center-ui--every-control)
8. [Preparing & using real datasets](#8-preparing--using-real-datasets)
9. [Complete API reference (inputs & outputs)](#9-complete-api-reference-inputs--outputs)
10. [Per-module verification](#10-per-module-verification)
11. [Complete end-to-end workflow (real-world)](#11-complete-end-to-end-workflow-real-world)
12. [Troubleshooting](#12-troubleshooting)
13. [Security & responsible use](#13-security--responsible-use)
14. [Appendix — reference tables & glossary](#14-appendix--reference-tables--glossary)

---

## 1. System overview

HORUS Sentinel is an **autonomous intelligence analyst**. A swarm of specialized **passive**
agents gathers open-source intelligence, correlates every finding into a living **Intelligence
Knowledge Graph**, a **fine-tuned language model (Horus-OSINT)** reasons over it, and a **human
analyst validates** before any report is final — turning hours of manual analyst work into minutes.

### The four planes

```
CONTROL      → Scope & Authorization Engine + orchestrator (fan-out / converge pipeline)
COLLECTION   → OSINT · Geo-Event · Web/Infra · Threat-Intel agents (+ gated Active Recon)
KNOWLEDGE    → SQLite/PostgreSQL · in-process graph (networkx)/Neo4j · keyword/Chroma RAG
REASONING    → HORUS Brain (Ollama/Hugging Face) → risk scoring → human validation → Report
```

### Design guarantees

| Guarantee | How it is enforced |
|---|---|
| **Passive by default** | Only already-public data is consumed unless active recon is explicitly authorized. |
| **Authorization as a feature** | Every job runs under a signed Rules-of-Engagement (RoE); out-of-scope requests are refused with **HTTP 403**. |
| **Chain of custody** | Every finding is traceable to a source tool + timestamp (report section 9). |
| **Human-authoritative** | A report is `COMPLETED` only after an analyst **validate** action. |
| **Runs anywhere** | Heavy services (Neo4j, ChromaDB, Ollama, Postgres) are **optional accelerators**; absent → SQLite + networkx + keyword-RAG + offline grounded synthesis. PDF generation is pure-Python (no system libraries). |

### Two operating modes in the UI

- **OSINT-Recon** — assess a **domain** or a **region + timeframe**; produces a full 9-section
  intelligence report, a risk-colored knowledge graph, and a downloadable PDF.
- **Geo-Intel (HORUS reasoning)** — a live **chat** with the fine-tuned Horus-OSINT model; each
  answer can be **downloaded as a branded PDF/HTML report**.

---

## 2. Prerequisites & system requirements

### 2.1 Minimum (MVP — runs anywhere, no infrastructure)

| Requirement | Details |
|---|---|
| **OS** | Windows 10/11, Linux, or macOS |
| **Python** | **3.12 or newer** (the project sets `requires-python = ">=3.12"`). 3.13 also works. |
| **Git** | Any recent version |
| **RAM** | 2 GB free |
| **Disk** | ~500 MB (app + virtual environment) |
| **Network** | Outbound HTTPS/DNS — only needed for *real* OSINT lookups and the online model; the offline demo needs none |

> The MVP needs **no Docker, no database, and no API keys**. It falls back to SQLite, an
> in-memory graph, a keyword RAG retriever, and deterministic grounded synthesis.

### 2.2 Recommended (model-authored narratives + live chat)

| Requirement | Details |
|---|---|
| **Ollama** | Native install from <https://ollama.com/download> — serves the fine-tuned model locally. |
| **GPU** | NVIDIA GPU (e.g. RTX Ada 5000) strongly recommended for the 8B model; CPU works but is slow. |
| **Disk** | +~5 GB for the `Horus-OSINT` model weights |

### 2.3 Full stack (production-style, optional)

| Requirement | Details |
|---|---|
| **Docker + Docker Compose** | Brings up Postgres, Neo4j, Redis, ChromaDB, MinIO, Ollama, API, and a worker. |
| **RAM** | 8 GB+ recommended for the full container set |

---

## 3. Installation & setup

### 3.1 Clone the repository

```bash
git clone https://github.com/MahmoudAlyosify/horus-sentinel.git
```

> ⚠️ **Critical:** the application lives in a **nested folder**. After cloning you get a top-level
> `horus-sentinel/` directory that contains the docs **and** an inner `horus-sentinel/` with the
> actual app. **All commands below run from the inner folder.**

```bash
cd horus-sentinel/horus-sentinel      # <-- the inner folder; do not skip this
```

### 3.2 Create a virtual environment & install dependencies

**Windows (PowerShell):**
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt          # runtime deps
# For running the test suite and linters too:
pip install -r requirements-dev.txt
```

**Linux / macOS:**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt      # optional: tests + linters
```

**Or use the Makefile** (Linux/macOS/WSL/Git-Bash):
```bash
make install     # creates .venv and installs dev dependencies
```

### 3.3 Verify the install

```bash
python -c "import fastapi, uvicorn, fpdf, arabic_reshaper, bidi, networkx, sqlalchemy; print('deps OK')"
```
**Expected output:** `deps OK`

---

## 4. Environment configuration (`.env`)

The app runs on safe defaults **without** a `.env` file. To customize, copy the template:

```bash
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
```

> 🔒 `.env` is **git-ignored** — it is never committed. Your Hugging Face token and any API keys
> stay on your machine only.

### 4.1 Key settings

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | `development` \| `production` |
| `APP_HOST` / `APP_PORT` | `0.0.0.0` / `8000` | Bind address & port |
| `REPORT_LANGUAGE` | `ar` | Report & narrative language: `ar` (Arabic RTL) or `en` (English LTR) |
| `BRAIN_BACKEND` | `hybrid` | `hybrid` \| `hf_serverless` \| `hf_endpoint` \| `ollama` (see below) |
| `OLLAMA_ENDPOINT` | `http://localhost:11434` | Where the local model is served |
| `HORUS_MODEL_NAME` | `horus-osint` | Ollama model tag to call |
| `HF_TOKEN` | *(empty)* | Hugging Face token (entered via first-run modal or here) |
| `HF_MODEL_ID` | `mahmoudalyosify/Horus-OSINT` | The fine-tuned model id |
| `DATABASE_URL` | *(unset → SQLite)* | Set to a Postgres DSN for the full stack |
| `QUEUE_BACKEND` | `memory` | `memory` (in-process) or `redis` (scalable workers) |
| `WORKER_ENABLED` | `true` | Run an in-process async worker on startup |
| `RAG_BACKEND` | `keyword` | `keyword` (zero-dep) or `chroma` (semantic) |
| `GEO_CORPUS_PATH` | `data/geo_corpus.json` | Real GTD/GDELT corpus (falls back to the bundled sample) |
| `REPORT_OUTPUT_DIR` | `data/reports` | Where rendered reports are written |

### 4.2 Brain backend selection

| `BRAIN_BACKEND` | Behaviour |
|---|---|
| `hybrid` *(default)* | Try Hugging Face online first, then local Ollama, then offline synthesis. |
| `ollama` | **Sovereign** — self-hosted model only; nothing leaves the machine. **Recommended for this project's custom model.** |
| `hf_serverless` | Hugging Face Inference router only. *(Note: the custom `Horus-OSINT` model is not served on HF's serverless router, so this path returns model-unavailable; use `ollama`.)* |
| `hf_endpoint` | A dedicated HF Inference Endpoint URL only (`HF_ENDPOINT_URL`). |

> **Recommendation:** for reliable model-authored output, run **Ollama locally** and set
> `BRAIN_BACKEND=ollama` (or keep `hybrid` — it falls through to Ollama automatically).

---

## 5. Running the system

### 5.1 Start the API + Command Center

From the inner `horus-sentinel/` folder with the virtual environment active:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
Or, equivalently:
```bash
make run
```

**Expected startup log:**
```
INFO:     Started server process [...]
INFO:     Waiting for application startup.
... worker_started backend=memory
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5.2 Open the interfaces

| Interface | URL | What it is |
|---|---|---|
| **Command Center** | <http://localhost:8000/ui> | The full operator UI (assessments + chat) |
| **API docs (Swagger)** | <http://localhost:8000/docs> | Interactive API explorer |
| **Health probe** | <http://localhost:8000/health> | Liveness + brain backend snapshot |

> _Screenshot placeholder:_ **`[Figure 1 — Command Center home, OSINT-Recon mode]`**

### 5.3 Quick sanity check

```bash
curl http://localhost:8000/health
```
**Expected output (example):**
```json
{"status":"ok","service":"horus-sentinel","env":"development",
 "brain_backend":"hybrid","brain_model":"horus-osint",
 "hf_model_id":"mahmoudalyosify/Horus-OSINT","report_language":"en"}
```

---

## 6. Optional accelerators (model, Docker, API keys)

### 6.1 Serve the fine-tuned model with Ollama (recommended)

```bash
# 1. Install Ollama:  https://ollama.com/download
# 2. Pull the fine-tuned model (one-time; ~5 GB, uses the GPU):
ollama pull hf.co/mahmoudalyosify/Horus-OSINT
# 3. Confirm it is served:
ollama list                      # 'Horus-OSINT' should appear
curl http://localhost:11434/api/tags
```
The app **auto-detects** Ollama — no code change. With it running, reports and chat are
**model-authored** (`generated_by: horus-osint`); without it, they fall back to grounded
offline synthesis (`generated_by: offline-synthesis`).

> The Makefile shortcut: `make model-pull` (inside the Docker stack) or `make model-list`.

### 6.2 Full stack via Docker (optional)

```bash
cp .env.example .env
docker compose -f deploy/docker-compose.yml up -d --build     # or: make up
docker compose -f deploy/docker-compose.yml ps                # or: make ps
```
Brings up Postgres, Neo4j, Redis, ChromaDB, MinIO, Ollama, the API, and an async worker.
Stop with `make down` (keeps data) or `make down-hard` (wipes volumes).

### 6.3 Passive threat-intel API keys (all optional)

Add any you have to `.env` to enrich results (the tools degrade gracefully without them):
`SHODAN_API_KEY`, `CENSYS_API_ID`/`CENSYS_API_SECRET`, `VIRUSTOTAL_API_KEY`, `OTX_API_KEY`,
`ABUSEIPDB_API_KEY`, `HIBP_API_KEY`.

---

## 7. The Command Center UI — every control

Open <http://localhost:8000/ui>. The header shows the eagle brand, the slogan **"The eye that
never sleeps"**, a language toggle, a brain-status chip, and the two mode tabs.

> _Screenshot placeholder:_ **`[Figure 2 — Header: language toggle, brain chip, mode tabs]`**

### 7.1 Header controls

| Control | Action |
|---|---|
| **EN / ع** (language toggle) | Switches the whole UI (LTR/RTL), the model's narrative language, and the report language. |
| **Brain chip** (dot + label) | Shows online/offline model status; click to open the first-run setup modal (enter a Hugging Face token). |
| **OSINT-Recon** tab | The assessment workflow (left = controls, right = report/graph/custody). |
| **Geo-Intel** tab | The Horus-OSINT chat. |

### 7.2 OSINT-Recon controls (left panel)

| Control | Action |
|---|---|
| **Subject type** | `Domain (owned/authorized)` or `Region + timeframe`. |
| **Subject** | The domain (e.g. `example.com`) or region name (e.g. `Sinai`). |
| **Year from / Year to** | Timeframe (region subjects only). |
| **Analyst (RoE signer)** | Name recorded as the authorizing analyst. |
| **Active offensive recon** (checkbox) | Adds gated active sources — only for domains you own/are authorized to test. |
| **Generate RoE** | Previews the Rules-of-Engagement record that will authorize the job. |
| **Run Assessment** | Authorizes → collects → reasons → drafts the report (stops at validation). |
| **Run Guided Demo** | One-click, fully-offline demo on a safe region (Sinai 2018–2019). |

### 7.3 OSINT-Recon results (right panel — tabs)

| Tab | Content |
|---|---|
| **Report** | The Report Card: executive summary, context, threat assessment, prioritized findings (each mapped to MITRE ATT&CK), conclusion, and a **Download PDF** button. |
| **Graph** | The risk-colored Intelligence Knowledge Graph (interactive). |
| **Custody** | The chain-of-custody log: every external touch, source, and timestamp. |

> _Screenshot placeholder:_ **`[Figure 3 — Report card + risk-colored knowledge graph]`**

### 7.4 Geo-Intel chat controls

| Control | Action |
|---|---|
| **Question box** | Type any intelligence/geopolitical question. |
| **Send** | Sends the question to the live Horus-OSINT model; the answer streams into the chat. |
| **⬇ Download report (PDF)** (per answer) | Downloads that Q&A as a branded PDF report. Every chat answer is stamped **"model reasoning — not corpus-grounded."** |

> _Screenshot placeholder:_ **`[Figure 4 — Geo-Intel chat with a Download report link under an answer]`**

---

## 8. Preparing & using real datasets

HORUS Sentinel operates on two kinds of real-world data.

### 8.1 Live OSINT on real domains (no dataset file needed)

For a **domain** subject the agents perform **real passive lookups** over the network:

| Agent | Real sources it queries |
|---|---|
| **OSINT** | DNS (A/AAAA/NS/MX), RDAP/WHOIS, Certificate Transparency (crt.sh) |
| **Web/Infra** | One polite HTTPS fingerprint of the site |
| **Threat-Intel** | OSV (CVE correlation) + optional reputation feeds (if API keys set) |

**How to use:** point an assessment at a domain **you own or are explicitly authorized to test**.
Public, well-known domains (e.g. `github.com`, `cloudflare.com`, `wikipedia.org`) are safe targets
for a passive demo — the tool only reads public records and sends one benign request.

### 8.2 Geo-event corpus (GTD/GDELT-derived) for region subjects

Region assessments read a JSON corpus of geopolitical events. A **sample** ships in the box:

- **Bundled sample:** `data/geo_corpus.sample.json` — covers **Sinai, Levant, Sahel, Cairo (2018–2019)**.
- **Your real corpus:** drop a full GTD/GDELT-derived file at `data/geo_corpus.json` (or point
  `GEO_CORPUS_PATH` at it). The Geo-Event agent uses it automatically.

**Corpus row shape (real dataset format):**
```json
{
  "region": "Sinai",
  "country": "Egypt",
  "year": 2018,
  "severity": "Low",
  "instability_index": 0.78,
  "modalities": ["armed assault", "bombing/explosion", "IED"],
  "targets": ["military", "police"],
  "summary": "..."
}
```

> **Tip:** to assess a region/timeframe, use one covered by your corpus. Regions/years **not** in
> the corpus return no geo events (an honest empty result), not an error.

### 8.3 The Rules-of-Engagement (RoE) — the authorization "dataset"

Every job requires a signed RoE. This is the input that makes collection legal and auditable:

```json
{
  "subject": "example.com",
  "enabled_sources": ["public_records", "web_infra", "threat_intel"],
  "in_scope_domains": ["example.com"],
  "active_authorized": false,
  "signed_by": "analyst_name",
  "expires_at": "2026-07-16T21:00:00Z"
}
```

---

## 9. Complete API reference (inputs & outputs)

Base URL: `http://localhost:8000`. Full interactive docs at `/docs`.

| Method & path | Purpose |
|---|---|
| `GET /` | Root — message, slogan, tagline |
| `GET /health` | Liveness + brain backend snapshot |
| `GET /setup/status` | First-run status + per-transport reachability |
| `POST /setup/hf-token` | Validate & save a Hugging Face token |
| `POST /setup/language` | Set language (`ar` \| `en`) |
| `POST /jobs` | Authorize & create a job (**403** if out of scope) |
| `GET /jobs` | List recent jobs |
| `GET /jobs/{id}` | Retrieve one job |
| `POST /jobs/{id}/run` | Run collection + reasoning (stops at validation) |
| `POST /jobs/{id}/enqueue` | Queue for async worker processing |
| `GET /jobs/{id}/report` | Get the Report Card + rendered graph |
| `POST /jobs/{id}/validate` | Record an analyst action (`validate` \| `flag` \| `edit`) |
| `GET /jobs/{id}/download/{fmt}` | Download the report (`pdf` \| `html` \| `json`) |
| `POST /demo` | Run the one-click guided demo end-to-end |
| `POST /chat` | Ask the Horus-OSINT model a free-form question |
| `POST /chat/report` | Render a chat Q&A as a downloadable report (`pdf` \| `html`) |

### 9.1 Create a job — `POST /jobs`

**Input:**
```json
{
  "subject": { "type": "domain", "value": "example.com" },
  "roe": {
    "subject": "example.com",
    "enabled_sources": ["public_records", "web_infra", "threat_intel"],
    "in_scope_domains": ["example.com"],
    "signed_by": "analyst_name",
    "expires_at": "2026-07-16T21:00:00Z"
  }
}
```
**Output (201):** `{ "id": "<job_id>", "status": "authorized", "message": "Job authorized and queued." }`
**Refusal (403):** out-of-scope `web_infra` → `{ "detail": "web_infra is enabled but '...' is not in in_scope_domains ..." }`

### 9.2 Report card — `GET /jobs/{id}/report`

**Output (abridged):**
```json
{
  "report_card": {
    "subject": "example.com",
    "generated_by": "horus-osint",
    "executive_summary": "...", "geopolitical_context": "...",
    "threat_assessment": "...", "conclusion": "...",
    "top_band": "Low", "entity_count": 10, "critical_cve_hits": 0,
    "prioritized_findings": [
      { "title": "Service example.com:443", "risk_band": "Low", "risk_score": 37.0,
        "framework": { "framework": "MITRE ATT&CK", "technique_id": "T1592",
                       "technique_name": "Gather Victim Host Information", "tactic": "Reconnaissance" },
        "recommendation": "...", "evidence_ids": ["..."] }
    ]
  },
  "graph": {
    "nodes": [ { "data": { "id": "Domain:example.com", "label": "example.com",
                           "kind": "Domain", "risk_band": "Low", "risk_score": 33.6, "color": "#2e8b57" } } ],
    "edges": [ { "data": { "source": "Domain:example.com", "target": "IP:...", "label": "RESOLVES_TO" } } ]
  }
}
```

### 9.3 Chat — `POST /chat`

**Input:** `{ "query": "What was the situation in Egypt during 2013?", "language": "en" }`
**Output:** `{ "answer": "...", "generated_by": "horus-selfhosted", "grounded": false }`
*(`generated_by` is `offline` if no model is reachable — a graceful message is still returned.)*

### 9.4 Chat report download — `POST /chat/report`

**Input:**
```json
{ "question": "...", "answer": "...", "generated_by": "horus-selfhosted",
  "language": "en", "fmt": "pdf" }
```
**Output:** a downloadable file — `Content-Type: application/pdf` (or `text/html`),
`Content-Disposition: attachment; filename=horus-chat-report.pdf`.

---

## 10. Per-module verification

Run these to confirm each module is healthy. All commands run from the inner `horus-sentinel/`
folder with the virtual environment active.

### 10.1 Unit & integration tests (all modules, offline)

```bash
pytest -q                     # or: make test
```
**Expected:** `104 passed` (network is mocked; no services required).

### 10.2 Lint & format

```bash
ruff check . && ruff format --check .        # or: make lint
```
**Expected:** `All checks passed!` and `96 files already formatted`.

### 10.3 Module-by-module live checks (server running)

| Module | Command | Expected |
|---|---|---|
| **API / Control** | `curl http://localhost:8000/health` | `{"status":"ok", ...}` |
| **Setup / Brain status** | `curl http://localhost:8000/setup/status` | JSON with `ollama_ready`, `hf_token_valid` |
| **Orchestrator + all agents** | `curl -X POST http://localhost:8000/demo` | `{"status":"completed","entity_count":4,...}` |
| **Reporting (PDF)** | `curl -L -o r.pdf http://localhost:8000/jobs/<demo_id>/download/pdf` | a file starting with `%PDF-` |
| **Authorization gate** | submit an out-of-scope `web_infra` job | **HTTP 403** |
| **Chat / model** | `curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"query":"hello","language":"en"}'` | `{"answer":"...","generated_by":"horus-selfhosted"}` |
| **Chat report** | `POST /chat/report` with `fmt:"pdf"` | a `%PDF-` file |

### 10.4 One-shot verification script

```bash
make verify        # health probe + guided demo end-to-end
```
**Expected:** health OK, then a completed demo job with an entity count and report URL.

---

## 11. Complete end-to-end workflow (real-world)

This is the full analyst workflow on **live data**, exactly as verified. It uses `example.com`
(an IANA-reserved domain designated for testing — safe and authorized for passive recon). To use
a domain you own, substitute it everywhere and ensure it is in `in_scope_domains`.

> Prereq: the server is running (Section 5). For model-authored narrative, Ollama is serving the
> model (Section 6.1); otherwise the narrative is grounded offline synthesis — still a full report.

### Step 1 — Authorize (create the job under a signed RoE)

```bash
curl -s -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "subject": {"type":"domain","value":"example.com"},
    "roe": {"subject":"example.com",
            "enabled_sources":["public_records","web_infra","threat_intel"],
            "in_scope_domains":["example.com"],
            "signed_by":"analyst_demo",
            "expires_at":"2026-07-16T23:00:00Z"}
  }'
```
**Output:** `{"id":"<JOB_ID>","status":"authorized", ...}` — copy the `id`.

### Step 2 — Run the multi-agent pipeline

```bash
curl -s -X POST http://localhost:8000/jobs/<JOB_ID>/run
```
**Output (example):**
```json
{"status":"awaiting_validation","agents_run":["osint","web_infra","threat_intel"],
 "entity_count":10,"critical_cve_hits":0,"errors":[]}
```
The pipeline runs `osint → web_infra → threat_intel → analysis`, then **pauses for human validation**.

### Step 3 — Review the report card + knowledge graph

```bash
curl -s http://localhost:8000/jobs/<JOB_ID>/report
```
**Output:** the Report Card (executive summary, threat assessment, ATT&CK-mapped prioritized
findings) and the graph (nodes = domain/IPs/services/tech; edges = `RESOLVES_TO`, `EXPOSES`,
`RUNS`, …). *In the UI, open the **Report**, **Graph**, and **Custody** tabs.*

### Step 4 — Analyst validation (makes it final)

```bash
curl -s -X POST http://localhost:8000/jobs/<JOB_ID>/validate \
  -H "Content-Type: application/json" \
  -d '{"action":"validate","analyst":"analyst_demo","note":"Reviewed; accurate."}'
```
**Output:** `{"action":"validate","new_status":"completed","is_final":true}`

### Step 5 — Download the signed report (PDF)

```bash
curl -L -o horus-report.pdf http://localhost:8000/jobs/<JOB_ID>/download/pdf
```
**Output:** a real PDF (`%PDF-`), ~30 KB, in Arabic (RTL) or English (LTR) per `REPORT_LANGUAGE`.
JSON and HTML are available too: `.../download/json`, `.../download/html`.

### Step 6 — Ask the analyst chat & download a chat report

```bash
# Ask a question
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Summarize the exposure of example.com","language":"en"}'

# Download that Q&A as a branded PDF report
curl -s -X POST http://localhost:8000/chat/report \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize the exposure of example.com",
       "answer":"<paste the answer here>","generated_by":"horus-selfhosted",
       "language":"en","fmt":"pdf"}' -o horus-chat-report.pdf
```

### Verified real-world results (reference)

Assessments run during verification (passive OSINT, live network):

| Target | Entities | IPs | Findings | Top band | PDF |
|---|---|---|---|---|---|
| `example.com` | 10 | 4 | 6 | Low | ✅ |
| `github.com` | 12 | 1 | 2 | Low | ✅ |
| `cloudflare.com` | 13 | 4 | 6 | Low | ✅ |
| `wikipedia.org` | 8–12 | 2 | 3–6 | Low | ✅ |
| `Sinai` (region, 2018–19) | 4 | — | — | Low | ✅ |

> _Screenshot placeholder:_ **`[Figure 5 — Downloaded Arabic RTL intelligence PDF]`**

---

## 12. Troubleshooting

| Symptom | Cause & fix |
|---|---|
| `ModuleNotFoundError` / `uvicorn: command not found` | You are in the wrong folder or the venv is not active. `cd` into the **inner** `horus-sentinel/horus-sentinel` and activate `.venv`. |
| `python: No such file` / syntax errors on start | Python < 3.12. Install **Python 3.12+** and recreate the venv (`py -3.12 -m venv .venv`). |
| Nothing at `/ui` | Ensure the server is running and you opened `http://localhost:8000/ui` (with `/ui`). |
| `[Errno 48/98] address already in use` | Port 8000 is taken. Run on another port: `uvicorn api.main:app --port 8010`. |
| Report shows `generated_by: offline-synthesis` | The model isn't reachable. Start **Ollama** and `ollama pull hf.co/mahmoudalyosify/Horus-OSINT` (Section 6.1). The report is still valid — just grounded-synthesis, not model-authored. |
| Chat returns `generated_by: offline` | Same as above — no model reachable; a graceful message is returned. |
| Arabic chat is slow / times out | The fine-tuned model is English-centric; Arabic prompts can be slow and may hit the 120 s timeout under load, then fall back to the offline message. English chat is fast. Increase `OLLAMA_TIMEOUT_S` in `.env` if needed. |
| PDF download returns a tiny (~63-byte) response | You are on an **older build**. Current builds render PDFs with a pure-Python engine (fpdf2) for **both** languages — no WeasyPrint/GTK needed. Pull the latest code. |
| `WeasyPrint could not import ... gobject-2.0-0` in logs | Harmless — WeasyPrint's native libs are absent, but the app uses the pure-Python PDF engine instead. |
| HF token rejected / `hf_serverless` gives no answer | The custom `Horus-OSINT` model isn't on HF's serverless router. Use **`BRAIN_BACKEND=ollama`** (local) — that is the supported model path. |
| Region assessment finds nothing | The region/timeframe isn't in the geo corpus. The sample covers **Sinai/Levant/Sahel/Cairo, 2018–2019**; add rows to `data/geo_corpus.json`. |
| `403` when submitting a domain job | **By design** — the domain isn't in `in_scope_domains`, or the RoE expired. Add the domain to scope and set a future `expires_at`. |
| Tests fail with Hugging Face routing errors | You are on an old build; current tests are hermetic (they pin the offline backend). Pull the latest and re-run `pytest`. |
| Arabic text prints as `?`/garbled in a Windows terminal | Cosmetic console limitation (cp1252). The PDF/HTML/UI render Arabic correctly; set `PYTHONIOENCODING=utf-8` for console scripts. |
| Reset to a clean state | `make clean` removes caches, the local SQLite DB, and generated reports. |

---

## 13. Security & responsible use

- **Passive & defensive by design.** Only already-public data is consumed unless you explicitly
  authorize active reconnaissance in the RoE **and** the target is in `in_scope_domains`.
- **Authorized targets only.** Point domain assessments at assets you **own or are cleared to
  test**. Out-of-scope requests are refused with **403**.
- **Active recon is double-gated:** it runs only when `active_authorized: true` **and** the target
  is in `in_scope_domains` — discovery/enumeration only, no exploitation, no payloads.
- **Chain of custody + human validation** make every report auditable and analyst-authoritative.
- See [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md).

---

## 14. Appendix — reference tables & glossary

### 14.1 Subject types

| Type | Value example | Drives |
|---|---|---|
| `domain` | `example.com` | OSINT · Web/Infra agents |
| `region` | `Sinai` (+ `year_from`/`year_to`) | Geo-Event agent |
| `org` | an organization name | (org workflows) |
| `entity` | a public threat entity | (entity workflows) |

### 14.2 Source categories (RoE `enabled_sources`)

| Category | Type | What it does |
|---|---|---|
| `public_records` | passive | DNS, RDAP/WHOIS, Certificate Transparency |
| `geo_events` | passive | GTD/GDELT-derived event context |
| `web_infra` | passive | Web fingerprinting (in-scope domains only) |
| `threat_intel` | passive | CVE correlation + reputation feeds |
| `active_recon` | **active** | Port scan + service/banner + active DNS enum *(gated)* |
| `web_crawl` | **active** | Compliant crawler/scraper *(gated)* |

### 14.3 Risk bands

`Critical` (red) · `High` (orange) · `Medium` (amber) · `Low` (green) · `Info` (grey).

### 14.4 Validation actions

| Action | Effect |
|---|---|
| `validate` | Report becomes `COMPLETED` (final). |
| `flag` | Report kept as draft, flagged for review. |
| `edit` | Analyst edit recorded; stays a draft. |

### 14.5 Report formats & outputs

| Format | Endpoint | Notes |
|---|---|---|
| **PDF** | `/jobs/{id}/download/pdf` | Pure-Python, Arabic RTL or English LTR, any OS |
| **HTML** | `/jobs/{id}/download/html` | Interactive report (embeds the graph) |
| **JSON** | `/jobs/{id}/download/json` | Full machine-readable context |

### 14.6 Glossary

- **RoE (Rules of Engagement)** — the signed authorization record every job runs under.
- **Report Card** — the structured intelligence output (narrative + prioritized findings + metrics).
- **Knowledge Graph** — the correlated entities/relationships, risk-colored.
- **Chain of custody** — the ordered log of every external touch with source + timestamp.
- **Brain / transport** — the reasoning backend (Ollama / Hugging Face / offline synthesis).

---

<div align="center">

**HORUS SENTINEL** · *The eye that never sleeps.*
Built for **authorized, defensive** use. Passive · auditable · human-validated.

</div>
