<div align="center">

# 🦅 HORUS SENTINEL

### Autonomous, Multi-Agent OSINT & Threat-Intelligence Platform

*"ARGUS's hundred eyes gather the intelligence — the Eye of HORUS delivers the judgment."*


[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org)
[![Model on HF](https://img.shields.io/badge/🤗%20Model-Horus--OSINT-yellow.svg)](https://huggingface.co/mahmoudalyosify/Horus-OSINT)

**ITC-Egypt 2026 · Track 3 — Intelligent Software Systems · Air Defence College**
<img width="1448" height="1086" alt="ITC-2026-T3-0726" src="https://github.com/user-attachments/assets/e2ee8bab-5ddb-430e-a475-fe273a4ab1da" />

</div>

---

## What it is

HORUS Sentinel is an **autonomous intelligence analyst**. A swarm of specialized, **passive** agents continuously gathers open-source intelligence, correlates every finding into a living **Intelligence Knowledge Graph**, and a **self-hosted, fine-tuned language model** reasons over it to deliver **prioritized, evidence-backed intelligence reports** — turning hours of manual analyst work into minutes.

It is built on the award-winning [`Horus-OSINT`](https://huggingface.co/mahmoudalyosify/Horus-OSINT) fine-tuned model, elevated from a chatbot into the reasoning core of a full multi-agent platform.

## What it is NOT

It is **passive and defensive by design**. It consumes only already-public data, never touches third-party infrastructure, enforces a hard authorization gate, keeps a full chain of custody, and **stops at recommendation** with a human analyst validating every report. See [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md).

---

## The four planes

```
CONTROL      → Scope & Authorization Engine + LangGraph orchestrator
COLLECTION   → OSINT · Geo-Event · Web/Infra · Threat-Intel agents (ARGUS "eyes")
KNOWLEDGE    → PostgreSQL · Neo4j graph · ChromaDB (RAG) · Redis · object store
REASONING    → HORUS Brain (self-hosted fine-tuned Llama-3) → risk scoring →
               human validation → structured Intelligence Report (PDF/HTML/JSON)
```

*(Full architecture in [`docs/`](docs/) and the master plan.)*

---

## Why it stands out

| Capability | Detail |
|---|---|
| 🧠 **Self-hosted fine-tuned brain** | Your own Llama-3-8B (QLoRA) via Ollama — data never leaves your infrastructure |
| 🕸️ **Intelligence Knowledge Graph** | Findings become a queryable Neo4j graph, risk-colored |
| 🤖 **Multi-agent orchestration** | Stateful, checkpointed LangGraph workflow (fan-out / converge) |
| 📚 **RAG-grounded reasoning** | MITRE ATT&CK + geo-threat corpus reduce hallucination |
| 🔒 **Authorization as a feature** | Signed RoE record required; passive-by-default |
| 🧾 **Chain of custody** | Every claim traceable to a source + timestamp |
| 👤 **Human-authoritative** | Analyst validates before any report is final |
| 💸 **~$5 cloud footprint** | Aggressive FinOps + free-tier fine-tuning |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/MahmoudAlyosify/horus-sentinel.git
cd horus-sentinel

# 2. Configure
cp .env.example .env         # then fill in the values

# 3. Bring up the stack (Postgres, Neo4j, Redis, ChromaDB, MinIO, Ollama)
docker compose -f deploy/docker-compose.yml up -d

# 4. Load the fine-tuned model into Ollama (one-time)
docker exec -it deploy-ollama-1 ollama pull hf.co/mahmoudalyosify/Horus-OSINT
#   (or copy your GGUF and: ollama create horus-osint -f Modelfile)

# 5. Python environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# 6. Run the API
uvicorn api.main:app --reload
#   → http://localhost:8000/docs
```

---

## Repository layout

```
horus-sentinel/
├── horus-geointel/   # the award-winning project, preserved & FROZEN
├── api/              # FastAPI app + routes
├── core/             # authorization engine, audit, rate limiting
├── agents/           # OSINT · Geo-Event · Web/Infra · Threat-Intel · Analysis · Report
├── tools/            # IntelTool ABC + external integrations
├── graph/            # Intelligence Knowledge Graph models + queries
├── scoring/          # deterministic risk-scoring engine
├── rag/              # ATT&CK + geo corpus embeddings + retrieval
├── horus_brain/      # bridge to the self-hosted fine-tuned model
├── workflows/        # LangGraph orchestration
├── reporting/        # Jinja2 → PDF/HTML/JSON renderers
├── schemas/          # Pydantic models (SentinelState, RoE, findings)
├── horus-ui/         # React + Cytoscape Command Center
├── deploy/           # docker-compose, IaC
└── tests/
```

> **Team rule:** `horus-geointel/` is **frozen** — the winning project is preserved as-is. Build around it, never inside it.

---

## Team

| Member | |
|---|---|
| **Mahmoud Alyosify** | [🤗](https://huggingface.co/mahmoudalyosify) · [GitHub](https://github.com/MahmoudAlyosify) |
| **Mirna Imbabi** | |
| **Sondos Hashem** | |

**Supervisor:** Sarah Mohammed Taha Khater · **Project ID:** ITC-2026-T3-0726

---

## License

MIT — see [`LICENSE`](LICENSE). Built for **authorized, defensive** use only.
