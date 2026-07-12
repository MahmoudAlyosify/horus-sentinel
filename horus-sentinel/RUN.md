# RUN — HORUS Sentinel on the GPU box (RTX Ada 5000)

Everything is already built and committed. This is the **install + run** runbook for the
work machine. Two paths: a **fast MVP** (no infra, verifies everything in minutes) and the
**full stack** (self-hosted model + graph/vector DBs).

> The code degrades gracefully: Neo4j, ChromaDB, WeasyPrint, LangGraph and Ollama are
> **optional accelerators**. Absent → SQLite + networkx + keyword-RAG + offline synthesis.
> Present → they light up automatically. You never edit code to switch.

---

## NEW in this version — online brain, Arabic, real PDF

- **The brain is pluggable** (`BRAIN_BACKEND`): `hybrid` (default — Hugging Face online, then
  local Ollama), `hf_serverless`, `hf_endpoint`, or `ollama` (sovereign, nothing leaves the box).
- **First-run setup asks for your Hugging Face token.** On first launch the Command Center shows
  a setup modal; enter your HF token → it's validated against HF and saved to `.env`. Or run the
  CLI wizard: `python -m core.setup_wizard`. Get a token at https://huggingface.co/settings/tokens
  (read scope). Without a token the platform still runs (offline synthesis / local Ollama).
- **Reports are Arabic (RTL) by default** (`REPORT_LANGUAGE=ar`; set `en` for English). The model
  is prompted to write the narrative in Arabic; section anchors stay machine-stable.
- **Real Arabic PDF** — produced by a pure-Python engine (fpdf2 + arabic-reshaper + python-bidi +
  bundled Amiri font), so a correct RTL PDF is generated on **any OS with no system libraries**.
  Download it from the UI ("⬇ تحميل تقرير PDF عربي") or `GET /jobs/{id}/download/pdf`.

> **Data-sovereignty note (important for an intelligence user):** `hybrid`/`hf_*` send the
> already-public grounded facts to Hugging Face's cloud. For a fully sovereign deployment set
> `BRAIN_BACKEND=ollama` — the same report, nothing leaves your infrastructure.

---

## 0. Prerequisites
- Python **3.12** (the code targets 3.12; 3.13 also works).
- (Full stack only) Docker + Docker Compose, and the RTX Ada 5000 for Ollama.
- Git.

---

## 1. Fast MVP — verify the whole system in ~3 minutes (no Docker, no keys)

```bash
git clone https://github.com/MahmoudAlyosify/horus-sentinel.git
cd horus-sentinel/horus-sentinel          # the project lives in the nested folder

python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# Git Bash / Linux:    source .venv/bin/activate

pip install -r requirements-dev.txt        # full deps (includes langgraph, chroma, weasyprint)
#   Minimal alternative (no heavy deps, still fully runs the MVP):
#   pip install fastapi "uvicorn[standard]" pydantic pydantic-settings python-dotenv \
#       httpx tenacity structlog sqlalchemy dnspython jinja2 networkx pytest pytest-asyncio respx ruff

# Run the tests (all pass offline, network mocked)
pytest -q
ruff check . && ruff format --check .

# Launch the platform
uvicorn api.main:app --reload
```

Open:
- **Command Center** → http://localhost:8000/ui  → click **"Run Guided Demo"** (fully offline, real report + graph)
- **API docs** → http://localhost:8000/docs
- **Refusal demo** → try a job whose RoE enables `web_infra` for an out-of-scope domain → **403 by design**

---

## 2. Full stack — self-hosted fine-tuned model + graph/vector DBs

```bash
cd horus-sentinel/horus-sentinel
cp .env.example .env            # fill in any API keys you have (all optional)

# 2a. Bring up Postgres, Neo4j, Redis, ChromaDB, MinIO, Ollama, and the API itself
docker compose -f deploy/docker-compose.yml up -d --build

# 2b. Load the fine-tuned model into Ollama (uses the GPU). One-time. Service-based (any OS):
docker compose -f deploy/docker-compose.yml exec ollama ollama pull hf.co/mahmoudalyosify/Horus-OSINT
#     From a local GGUF + Modelfile:
#     docker compose -f deploy/docker-compose.yml cp ./Horus-OSINT.gguf ollama:/root/
#     docker compose -f deploy/docker-compose.yml exec ollama sh -c 'printf "FROM /root/Horus-OSINT.gguf\n" > /root/Modelfile && ollama create horus-osint -f /root/Modelfile'
#
#     WINDOWS + RTX (recommended, easiest GPU): install native Ollama for Windows, run
#       ollama pull hf.co/mahmoudalyosify/Horus-OSINT
#     then set  OLLAMA_ENDPOINT=http://host.docker.internal:11434  in .env and re-run 2a.

# 2c. Async workers are included: the compose file runs a `worker` service (QUEUE_BACKEND=redis)
#     that pulls queued jobs and runs them resumably. Scale them:  docker compose up -d --scale worker=3
#     Submit async:  POST /jobs  ->  POST /jobs/{id}/enqueue   (a worker picks it up)

# 2d. (Optional) drop the real GTD/GDELT corpus in so the Geo-Event agent uses it:
#     copy your file to  ./data/geo_corpus.json   (the sample is used until you do)

# 2e. Verify
curl http://localhost:8000/health
#   → open http://localhost:8000/ui and run an assessment; the brain now narrates via Ollama
```

Confirm the model is served:
```bash
docker compose -f deploy/docker-compose.yml exec ollama ollama list   # horus-osint should appear
curl http://localhost:11434/api/tags                # HTTP 200 (PowerShell: use curl.exe)
```

---

## 3. GPU note (Ollama + RTX Ada 5000)

**Windows 11 (this box) — recommended:** install the **native Ollama for Windows** app
(https://ollama.com/download). It uses the RTX directly with zero extra config. Then set
`OLLAMA_ENDPOINT=http://host.docker.internal:11434` in `.env` so the containers reach it.
This avoids WSL2 GPU‑passthrough setup entirely.

**Docker‑GPU (Linux, or Windows with WSL2 GPU):**
`ollama/ollama:latest` uses the GPU automatically when the NVIDIA Container Toolkit is
installed. If containers can't see the GPU, install `nvidia-container-toolkit` (Linux) or
enable WSL2 GPU in Docker Desktop (Windows), and add to the `ollama` service in
`deploy/docker-compose.yml`:

```yaml
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

Running Ollama **natively** on the host (not in Docker) also works — just set
`OLLAMA_ENDPOINT=http://host.docker.internal:11434` for the API container, or run the API
natively too.

---

## 4. Verify checklist (what "working" looks like)
- [ ] `pytest` green (~85 tests).
- [ ] `/ui` loads in **Arabic (RTL)**; **العرض الإرشادي** produces a report card + risk-colored graph.
- [ ] First run shows the **HF token setup modal**; entering a valid token flips the brain chip to
      "أونلاين"; `GET /setup/status` shows `online_ready: true`.
- [ ] A `web_infra` job on an out-of-scope domain returns **403** (authorization gate).
- [ ] `GET /jobs/{id}/download/pdf` returns a real **Arabic RTL PDF**.
- [ ] Online brain: a run shows `generated_by: mahmoudalyosify/Horus-OSINT (HF ...)`;
      local: `generated_by: horus-osint`; neither reachable: `offline-synthesis`.
- [ ] A report is only **COMPLETED** after an analyst **validate** action.

---

## 5. Troubleshooting
| Symptom | Cause / fix |
|---|---|
| `generated_by: offline-synthesis` on full stack | Ollama not reachable or model not loaded — see step 2b. |
| PDF not produced | WeasyPrint system libs missing. The Docker image bundles them; locally, install GTK/Pango or just use HTML/JSON (auto-skipped, non-fatal). |
| Neo4j browser empty | The MVP graph is in-process; the Neo4j mirror is best-effort. Ensure the `neo4j` service is up and `NEO4J_*` env is set. |
| `psycopg` connect error | Check `DATABASE_URL` and that Postgres is healthy (`docker compose ps`). |
| Geo agent finds nothing | Region/timeframe not in the corpus. The sample covers Sinai/Levant/Sahel/Cairo 2018–2019; add rows to `data/geo_corpus.json`. |

---

*Built for authorized, defensive use. Passive · auditable · human-validated.*
