# HORUS SENTINEL
## An Autonomous, Multi-Agent OSINT & Threat-Intelligence Platform
### Master Specification & Ground-Up Build Plan — v1.0

> **Competition:** ITC-Egypt 2026 · Track 3 — Intelligent Software Systems · Air Defence College (Egyptian Military)
> **Project ID:** ITC-2026-T3-0726
> **Supervisor:** Sarah Mohammed Taha Khater
> **Team:** 3 members (Mahmoud, Mirna, Sondos) — waterfall, whole team on each task
> **Foundational asset:** the award-winning fine-tuned model `mahmoudalyosify/Horus-OSINT` (Llama-3-8B, QLoRA)
> **Strategic goal:** move from rank #20 to a **1st / 2nd place** finish
> **Chosen direction:** **Path C** — a *defensive, passive, OSINT-driven* threat-intelligence platform that keeps ARGUS's multi-agent architecture but points it at the domain the fine-tuned model is genuinely expert in.

---

## PART 0 — READ THIS FIRST: The Strategic Frame

### 0.1 The problem with the naïve merge (and why Path C wins)

The tempting move was to bolt an *active cyber-scanning* engine (ARGUS) onto the winning geopolitical chatbot. As your co-architect I blocked that, because it contains a contradiction a military judge will find in one question:

- Your model was fine-tuned on **GTD + GDELT** — historical terrorism and geopolitical event data (to ~2020). It reasons about **regions, threat actors, attack modalities, and geopolitical context**.
- Your own HuggingFace model card explicitly warns it is **not suited for critical security decisions** without expert validation.
- An *active network scanner* needs a model that reasons about **CVEs, ports, and services** — a completely different domain. Reusing the geopolitical model there is a scope mismatch, and demoing live scanning to military judges adds an ethics question you don't need.

**Path C resolves all of this.** We keep everything technically impressive about ARGUS — the multi-agent orchestration, the knowledge graph, the RAG grounding, the authorization engine, the structured reporting — but we point the collection agents at **open-source intelligence** (the model's actual home turf) instead of active infrastructure scanning. The result:

| Property | Why it wins for THIS competition |
|---|---|
| **Domain-honest** | The agents collect the same *kind* of signal the model was trained to reason about |
| **Passive & defensive** | Nothing touches anyone's infrastructure. This is a *blue-team analyst tool* — exactly what a defence college wants |
| **No scope contradiction** | The model card's warning becomes a *feature* (we built in expert-in-the-loop validation), not a liability |
| **Keeps the technical wow** | Multi-agent + graph + RAG + self-hosted fine-tuned brain — all intact |
| **Reuses the winning asset** | The fine-tuned model graduates from "chatbot" to "the reasoning core of an autonomous analyst platform" |

### 0.2 The one-sentence pitch (memorize it)

> **"HORUS Sentinel is an autonomous, multi-agent intelligence analyst: many specialized agents — the eyes of ARGUS — continuously gather open-source intelligence, correlate it into a living knowledge graph, and our self-hosted fine-tuned model — the Eye of HORUS — reasons over it to deliver prioritized, evidence-backed intelligence reports in minutes instead of days."**

Two mythologies, one honest system:
- **ARGUS** (Greek hundred-eyed giant, *Panoptes*) = the **collection swarm** — many eyes gathering OSINT.
- **HORUS** (Egyptian Eye that judges and protects, *"The Eye That Never Sleeps"* — your existing brand) = the **reasoning brain** that turns what the eyes saw into judgment.

### 0.3 What "intelligent, adaptable, practical" means here (mapping to the track)

The track asks for *"intelligent, adaptable and practical digital systems that address real-world challenges."* We hit all three explicitly:

- **Intelligent** — autonomous multi-agent reasoning with a fine-tuned domain model + RAG grounding, not a scripted pipeline.
- **Adaptable** — a pluggable tool/agent architecture; add a new intelligence source by writing one class. A pluggable LLM layer (self-hosted or cloud). Two operating modes from one brain.
- **Practical** — solves a documented real problem (analyst data-overload), produces a real deliverable (a structured intelligence report), and runs on a **$5 cloud budget** with a **self-hosted model** (data sovereignty — critical for a military user).

---

## PART 1 — The Problem, The Users, The Value

### 1.1 The real-world problem

Intelligence and security analysts drown in open-source data. To assess a single question — *"What is the threat picture around entity/region X?"* — an analyst manually pivots across dozens of disconnected sources: news streams, event databases, WHOIS/DNS records, certificate logs, breach corpora, social and technical databases, reputation feeds. Then they hold the fragments in their head and try to correlate them into an assessment. This is:

- **Slow** — hours to days per assessment.
- **Inconsistent** — coverage depends on which sources the analyst remembers to check.
- **Poorly correlated** — findings live in separate tabs; the *relationships* between them are reconstructed by hand.
- **Hard to prioritize** — raw findings vastly outnumber the few that matter.
- **Not reproducible** — two analysts produce two different assessments; there's no audit trail of *what was checked, when, from where*.

### 1.2 What HORUS Sentinel does

Given an authorized **subject of inquiry** (a region + timeframe, an organization, a domain you own, or a public threat entity) plus a signed **Rules-of-Engagement (RoE)** record, it:

1. **Collects** open-source intelligence through a swarm of specialized, passive agents.
2. **Correlates** every finding into a unified **Intelligence Knowledge Graph** (entities + relationships).
3. **Enriches** entities with reputation and contextual threat data.
4. **Reasons** over the graph with the fine-tuned HORUS model (RAG-grounded) to identify what matters, prioritize it, and map it to established frameworks (MITRE ATT&CK where cyber-relevant; structured threat taxonomy for geopolitical).
5. **Reports** a structured, evidence-backed, chain-of-custody intelligence deliverable (PDF / HTML / JSON) — with **every claim traceable to a source**, and an explicit **analyst-validation** step (honoring the model card's guidance).

### 1.3 Users & use cases

| User | Use case | Consumes |
|---|---|---|
| **Defence/intelligence analyst** | Rapid OSINT threat assessment of a region/entity/timeframe | The intelligence report |
| **SOC / blue team** | Monitor the org's *own* public exposure (defensive EASM-lite, passive only) | Exposure findings + graph |
| **CTI analyst** | Profile a public threat actor / infrastructure from open sources | Entity dossier |
| **Instructor / trainee (Air Defence College)** | A teachable, transparent analyst tool for training | The whole system, hands-on |

### 1.4 Why a military defence audience specifically likes this

- **Passive & sovereign** — it never attacks; it runs a self-hosted model so **no data leaves their infrastructure**.
- **Auditable** — every finding has a source and timestamp; every run has an authorization record. This is how real intelligence products are built.
- **Analyst-augmenting, not analyst-replacing** — the explicit human-validation step reflects operational reality and defuses the "can we trust the AI?" question before it's asked.

---

## PART 2 — System Architecture

### 2.1 The four planes (this is the mental model — memorize it)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HORUS SENTINEL                              │
│                                                                     │
│  ┌───────────────────────── CONTROL PLANE ──────────────────────┐   │
│  │  Scope & Authorization Engine (RoE, allowlist, rate budget)  │   │
│  │  Orchestrator (LangGraph stateful state machine)             │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                                 │ authorized job                     │
│  ┌───────────────── COLLECTION PLANE ("ARGUS eyes") ─────────────┐   │
│  │  OSINT Agent · Geo-Event Agent · Web/Infra Agent ·           │   │
│  │  Threat-Intel Agent      → all via Tool Abstraction Layer     │   │
│  │  (rate-limited · cached · audit-logged · passive-only)        │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                                 │ normalized findings                │
│  ┌───────────────────── KNOWLEDGE PLANE ────────────────────────┐   │
│  │  PostgreSQL (jobs/RoE/audit/findings)                        │   │
│  │  Neo4j  → Intelligence Knowledge Graph (entities + edges)    │   │
│  │  ChromaDB → RAG (MITRE ATT&CK + threat taxonomy + findings)  │   │
│  │  Redis (cache/queue) · Object store (immutable evidence)     │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                                 │ graph + retrieved context          │
│  ┌────────────────── REASONING & DELIVERY PLANE ────────────────┐   │
│  │  HORUS Brain (fine-tuned Llama-3, self-hosted via Ollama)    │   │
│  │  Analysis Agent (RAG-grounded reasoning) → risk scoring      │   │
│  │  Human-validation checkpoint → Reporting Agent               │   │
│  │  → structured Intelligence Report (PDF / HTML / JSON)         │   │
│  └───────────────────────────────────────────────────────────────┘  │
│                                 ▲                                    │
│                    HORUS Command Center (Unified Web UI)             │
└─────────────────────────────────────────────────────────────────────┘
```

**Core principle:** agents never pass big blobs to each other. Each agent writes normalized findings to the **Knowledge Plane** and passes only a reference. The graph is the single source of truth the brain reasons over. This keeps every step small, resumable, and auditable.

### 2.2 Design invariants (never violate these — they're what "production-grade" means)

1. **Passive by default; nothing touches a third party's infrastructure.** All collection consumes already-public data. No active scanning of systems you don't own. (Any owned-asset checks are still gated by RoE and default to your own domain.)
2. **No external call bypasses the Tool Abstraction Layer.** Rate-limit, cache, and audit are enforced centrally so no agent can skip them.
3. **No job runs without an authorization record.** The Scope & Authorization Engine is a hard gate, not a checkbox.
4. **The risk score is deterministic; the LLM explains it, never invents it.** Any model adjustment is bounded (±1 band), logged with a reason, and shown in the report.
5. **Every claim in the report is traceable to a source + timestamp (chain of custody).**
6. **A human analyst validates before a report is marked final** (honors the model card's guidance; turns a limitation into a designed control).

### 2.3 Orchestration (why LangGraph, not a linear script)

Intelligence gathering is a **fan-out / converge** problem with conditional re-entry: a new entity discovered by one agent becomes an input to others. We model this as a stateful graph:

- Nodes = agents; edges = transitions; a shared `SentinelState` carries `job_id`, the `AuthContext`, and lightweight references (not data).
- Conditional edges implement policy (e.g., an agent only runs if its source is enabled in the RoE and within rate budget).
- Checkpointing (Postgres) makes long jobs **resumable and auditable** — every transition is persisted.

```python
# workflows/sentinel_graph.py  (skeleton — orchestration only)
from langgraph.graph import StateGraph, END
from schemas import SentinelState

def build_sentinel_graph():
    g = StateGraph(SentinelState)

    g.add_node("authorize",     authorization_gate)   # validate RoE, classify scope
    g.add_node("osint",         osint_agent)          # passive public records
    g.add_node("geo_event",     geo_event_agent)      # region/timeframe event context
    g.add_node("web_infra",     web_infra_agent)      # passive infra/tech (owned or public)
    g.add_node("threat_intel",  threat_intel_agent)   # reputation + framework context
    g.add_node("analysis",      analysis_agent)       # HORUS brain, RAG-grounded
    g.add_node("validate",      human_validation_gate)# analyst-in-the-loop checkpoint
    g.add_node("report",        reporting_agent)

    g.set_entry_point("authorize")
    g.add_edge("authorize", "osint")
    g.add_edge("osint", "geo_event")
    g.add_edge("osint", "web_infra")
    g.add_edge("geo_event", "threat_intel")
    g.add_edge("web_infra", "threat_intel")
    g.add_edge("threat_intel", "analysis")
    g.add_edge("analysis", "validate")
    g.add_edge("validate", "report")
    g.add_edge("report", END)
    return g.compile(checkpointer=postgres_checkpointer)
```

### 2.4 The Tool Abstraction Layer (where the non-negotiable controls live)

Every external source implements one interface, so no agent can bypass the operational controls:

```python
class IntelTool(ABC):
    name: str
    classification: Literal["passive"]        # Path C: everything is passive
    source_category: str                       # "public_records" | "geo_events" | ...
    rate_limit: RateBudget                      # per-source token bucket
    cache_ttl: int                              # avoid re-querying public sources

    @abstractmethod
    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult: ...

    async def __call__(self, subject, ctx):
        ctx.assert_allows(self.classification, self.source_category, subject)  # raises if disallowed
        if cached := await cache.get(self.cache_key(subject)):
            return cached
        await self.rate_limit.acquire()
        result = await self.run(subject, ctx)
        await audit_log.record(self.name, subject, ctx, result.summary())  # chain of custody
        await cache.set(self.cache_key(subject), result, ttl=self.cache_ttl)
        return result
```

Three properties fall out for free: **rate-limiting / ToS compliance** enforced centrally, **caching** (politeness + the $5 cost story), and **every external touch audit-logged**.

---

## PART 3 — The Agents (Collection Plane in detail)

All agents share one contract: read a `Subject` + `AuthContext`, call tools through the abstraction layer, write **normalized findings** to the Knowledge Base, return a typed Pydantic result. All are **passive**.

### 3.1 OSINT Collection Agent
**Mission:** build the base entity picture from already-public records.
- **Tools:** WHOIS/RDAP, DNS (A/AAAA/MX/TXT/NS/CNAME), certificate transparency (crt.sh), passive subdomain discovery (public sources only), email-pattern inference, breach-corpus lookups via reputable APIs (e.g., HaveIBeenPwned), public code-repo metadata search.
- **Output (normalized):** organization, domains, subdomains (with source + resolved IPs), email pattern, public-profile references, exposed-artifact candidates.

### 3.2 Geo-Event Context Agent  *(this is where your existing strength shines)*
**Mission:** attach geopolitical / threat-event context to a region + timeframe — the exact capability your model was trained on.
- **Tools:** curated GTD/GDELT-derived local corpus (you already built the 159,826-pair dataset), plus optional live news/event APIs (passive, rate-limited).
- **Output:** for a region+year — instability indicators, dominant event/attack modalities, primary target categories, actor references, a threat-context summary. This becomes prime RAG material for the HORUS brain.

### 3.3 Web / Infrastructure Fingerprinting Agent  *(passive)*
**Mission:** characterize the public technology footprint of a web-facing entity (owned domain or public entity).
- **Tools:** polite HTTP(S) header + single-page fetch, fingerprint matching (framework/CMS/JS/CDN/WAF), favicon hashing, cloud-provider inference from IP ranges + headers + CNAME chains. Passive internet-scan data via Shodan/Censys APIs (reads pre-collected data — no packets to the target).
- **Output:** tech stack, CDN/WAF presence, cloud provider, TLS posture, version evidence (feeds CVE correlation).

### 3.4 Threat-Intelligence Enrichment Agent  *(passive)*
**Mission:** attach reputation and framework context.
- **Tools:** VirusTotal, AlienVault OTX, AbuseIPDB (reputation), NVD/OSV (known-CVE correlation for any discovered product+version — informational only), MITRE ATT&CK mapping.
- **Output:** normalized reputation score, indicator list, known-CVE references, candidate ATT&CK technique IDs (with emphasis on TA0043 Reconnaissance / TA0042 Resource Development — the *defensive* framing: "here is what an adversary could learn about you from open sources").

---

## PART 4 — The Reasoning Brain (your fine-tuned model, elevated)

### 4.1 The role of the HORUS model

Your fine-tuned `Horus-OSINT` model already produces a **structured, sectioned Intelligence Report Card** (GEOPOLITICAL CONTEXT → THREAT ASSESSMENT → CONCLUSION). In HORUS Sentinel it becomes the **Analysis Agent** — but now it reasons over a *correlated knowledge graph + RAG-retrieved context*, not a single free-text prompt. That is a large capability jump on top of the same model.

### 4.2 How reasoning works (RAG over the graph)

1. For the subject, retrieve the relevant **subgraph** (entity + 1–2 hop neighborhood) from Neo4j.
2. Retrieve grounding context from ChromaDB: relevant **MITRE ATT&CK** techniques (cyber-relevant subjects) and/or the **geo-threat corpus** (region/entity subjects).
3. Build a structured prompt: correlated facts + retrieved framework context → ask the model to produce the report card sections (context, assessment, prioritized findings, recommendations).
4. **Ground truth stays in the graph.** The model synthesizes and explains; it does not invent entities. Every finding references graph nodes/evidence IDs.

### 4.3 The provider bridge (the one clean integration point)

```python
# horus_brain/horus_provider.py
class HorusReasoningProvider(LLMProvider):
    """Wraps the fine-tuned Llama-3-8B served by Ollama (VPC-internal, port 11434).
       Same Intelligence Report Card DNA the model already produces — now graph-grounded."""
    name = "horus-selfhosted"
    endpoint = "http://ollama:11434/api/generate"
    model = "horus-osint"

    async def reason(self, subgraph: Subgraph, rag_context: str) -> ReportCard:
        prompt = build_intel_prompt(subgraph, rag_context)   # structured, grounded
        raw = await self._call_ollama(prompt)
        return ReportCard.parse(raw)                          # typed, sectioned
```

### 4.4 Deterministic risk scoring (the model explains, never invents)

```
RiskScore(entity) = w_e·Exposure + w_t·ThreatContext + w_i·ReputationIntel + w_c·Criticality
default weights:    w_e=0.30       w_t=0.30            w_i=0.20             w_c=0.20
```

- Deterministic formula → base score + band (Critical/High/Medium/Low/Info).
- The model may adjust **±1 band max**, must log the reason, and the adjustment is shown in the report. Reproducible: same inputs → same score.

### 4.5 Human-validation checkpoint (turning the model card warning into a feature)

Before a report is `FINAL`, an analyst sees the model's draft findings + the evidence and clicks **Validate** / **Flag** / **Edit**. This:
- Honors your model card's explicit guidance for security/military contexts.
- Matches how real intelligence products are signed off.
- Is a **selling point** to military judges, not an admission of weakness. Frame it as *"AI-augmented analyst, human-authoritative."*

---

## PART 5 — Knowledge Model (the Intelligence Knowledge Graph)

### 5.1 Node types
`Organization`, `Domain`, `Subdomain`, `IP`, `Service`, `Technology`, `Certificate`, `Email`, `Person`, `CVE`, `CloudAsset`, `Region`, `ThreatActor`, `Event`, `Indicator`.

### 5.2 Edge types (examples)
```
(Organization)-[:OWNS]->(Domain)
(Domain)-[:HAS_SUBDOMAIN]->(Subdomain)
(Subdomain)-[:RESOLVES_TO]->(IP)
(IP)-[:EXPOSES]->(Service)
(Service)-[:RUNS]->(Technology)
(Technology)-[:HAS_VULNERABILITY]->(CVE)
(Region)-[:HAS_EVENT]->(Event)
(ThreatActor)-[:ASSOCIATED_WITH]->(Event)
(Entity)-[:HAS_INDICATOR]->(Indicator)
```

### 5.3 Why a graph (the single strongest technical idea)
Once findings are a graph, analysis becomes **traversal**, not manual cross-referencing:
- *"Which public services run technology with a known critical CVE?"* → one Cypher query.
- *"Which entities share infrastructure or an actor with a high-risk event?"* → neighborhood query.
- The Analysis Agent retrieves **subgraphs** as grounded LLM context — far more reliable than dumping raw JSON into a prompt.
- The rendered, risk-colored graph is your **single most screenshot-worthy artifact** — put it on every slide, the report cover, and LinkedIn.

```cypher
// example: public services carrying a critical known vuln
MATCH (i:IP)-[:EXPOSES]->(s:Service)-[:RUNS]->(t:Technology)-[:HAS_VULNERABILITY]->(c:CVE)
WHERE c.cvss >= 9.0 AND i.internet_facing = true
RETURN i.address, s.port, t.name, c.id, c.cvss ORDER BY c.cvss DESC
```

---

## PART 6 — Output System

### 6.1 Report structure (9 sections)
1. **Executive Summary** — model-authored, non-technical: the picture in a paragraph + top 3–5 items + headline metrics.
2. **Subject & Scope** — what was assessed, the RoE, the sources enabled.
3. **Discovered Entities** — with source + timestamp.
4. **Context & Exposure** — geo-event context and/or public infra/tech footprint.
5. **Threat-Intelligence Enrichment** — reputation, indicators, known-CVE references.
6. **Intelligence Knowledge Graph** — rendered map (interactive in HTML, static in PDF), risk-colored.
7. **Risk Analysis** — matrix + per-finding score with component breakdown.
8. **Prioritized Findings & Recommendations** — each: evidence → why it matters → framework mapping → recommendation.
9. **Appendix (Chain of Custody)** — full evidence list with source attribution + collection times + the RoE + the analyst validation record.

### 6.2 Formats
- **PDF** (Jinja2 → WeasyPrint) — the deliverable.
- **HTML** — interactive, with the live graph viewer.
- **JSON** — machine-readable, for downstream tooling.

---

## PART 7 — Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.12 | Security + AI ecosystem |
| Backend / API | FastAPI + Uvicorn | Async, typed, auto OpenAPI docs |
| Orchestration | LangGraph (core) + LangChain (adapters) | Stateful, conditional, checkpointed graph |
| LLM layer | Provider-abstracted; **default = self-hosted fine-tuned Llama-3 via Ollama** | Data sovereignty + no vendor lock-in |
| Relational DB | PostgreSQL | Jobs, RoE, audit, findings |
| Graph DB | Neo4j (prod) / networkx (MVP) | Intelligence Knowledge Graph |
| Vector DB | ChromaDB | RAG over ATT&CK + geo corpus + findings |
| Cache / queue | Redis | Cache, rate budgets, task queue |
| Object store | MinIO (local) / S3 (cloud) | Immutable evidence |
| OSINT tools | WHOIS/RDAP, dnspython, crt.sh, Shodan, Censys, fingerprinting | Passive discovery |
| Threat intel | VirusTotal, OTX, AbuseIPDB, NVD/OSV, MITRE ATT&CK | Enrichment |
| Reporting | Jinja2 + WeasyPrint; Cytoscape.js/D3 | HTML→PDF + interactive graph |
| Frontend | React + Tailwind + Cytoscape.js | The Command Center UI judges will click |
| Deploy | Docker + docker-compose → AWS EC2/ECS (extend existing Terraform) | Reproducible, $5 story |
| Observability | Structured logging, Prometheus/Grafana | Production-grade signal |
| CI/CD | GitHub Actions (lint, type-check, test, security scan) | Portfolio polish |

---

## PART 8 — Repository Structure

```
horus-sentinel/
├── horus-geointel/            # ← THE WINNING PROJECT, MOVED IN WHOLE, FROZEN
│   ├── terraform/             #   existing IaC (extend elsewhere, don't edit here)
│   ├── fine-tuning/           #   existing Colab QLoRA notebook
│   ├── pyspark/               #   existing EMR pipeline
│   └── README.md              #   existing — it won; leave it
│
├── api/                       # FastAPI app, routes, job submission
├── core/
│   ├── authorization.py       # Scope & Authorization Engine + RoE model
│   ├── audit.py               # chain-of-custody logging
│   └── rate_limit.py          # token-bucket rate budgets
├── agents/
│   ├── osint_agent.py
│   ├── geo_event_agent.py     # ← leverages your GTD/GDELT strength
│   ├── web_infra_agent.py
│   ├── threat_intel_agent.py
│   ├── analysis_agent.py      # ← RAG-grounded reasoning
│   └── report_agent.py
├── tools/                     # IntelTool ABC + integrations
│   ├── base.py                # IntelTool ABC (rate-limit/cache/audit)
│   ├── whois_tool.py
│   ├── dns_tool.py
│   ├── crtsh_tool.py
│   ├── shodan_tool.py
│   ├── censys_tool.py
│   ├── fingerprint_tool.py
│   └── threatintel_tool.py
├── graph/                     # Intelligence Knowledge Graph models + queries
├── scoring/                   # deterministic risk-scoring engine
├── rag/                       # ATT&CK + geo corpus, embeddings, retrieval
├── horus_brain/
│   └── horus_provider.py      # ← the bridge: wraps your Ollama-served model
├── workflows/
│   └── sentinel_graph.py      # LangGraph orchestration
├── reporting/                 # Jinja2 templates, PDF/HTML/JSON renderers
├── schemas/                   # Pydantic: SentinelState, RoE, findings, Subject
├── horus-ui/                  # React + Cytoscape Command Center
│   ├── src/
│   │   ├── ModeSelector/      #   Geo-Intel | OSINT-Recon
│   │   ├── GeoIntelView/      #   your existing chat, preserved
│   │   ├── ReconView/         #   subject + RoE → live job → report
│   │   └── KnowledgeGraph/    #   Cytoscape viewer
│   └── Dockerfile             #   Nginx (as you already do)
├── deploy/                    # docker-compose for the whole stack
├── tests/
└── README.md                  # top-level unified story
```

**Team rule:** everything under `horus-geointel/` is **frozen**. Build around it, never inside it.

---

## PART 9 — The Ground-Up Build Plan (Waterfall, 3 People Together)

You work as **one team, sequentially, task by task**. So this is a single ordered backlog. Each phase ends with a demoable result and a git tag. Rotate three roles per task so everyone can answer anything in the viva:
- **Driver** (types) · **Navigator** (reviews live vs. the spec) · **Verifier** (runs it, confirms Definition of Done, writes the demo note)

> **Pacing:** phases are written to be flexible. Comfortable pace ≈ 2 weeks/phase; aggressive ≈ 1 week/phase. Set the pace to your real deadline. Phases 0–4 + 8 are the **minimum winning system**; 5–7 are depth/polish.

### PHASE 0 — Consolidation & Environment  *(~2–3 days)*
**Goal:** one repo, winning project preserved, everyone runs everything locally.

| Task | DoD |
|---|---|
| 0.1 Create `horus-sentinel` monorepo; move winning project into `horus-geointel/` untouched | Old project still runs identically as a subfolder |
| 0.2 `docker-compose`: Postgres, Redis, Neo4j, Ollama serving your model | `docker-compose up` runs all; `curl` to Ollama returns a report card |
| 0.3 Top-level README skeleton + architecture diagram + the one-sentence pitch | README tells the ARGUS-feeds-HORUS story |
| 0.4 CONTRIBUTING + branch strategy + conventional-commit convention agreed | All three can commit cleanly |

**Tag:** `v0.1-foundation` · **Demo:** "The winning project, intact, inside the platform, brain running locally."

### PHASE 1 — Control Plane (Authorization = the maturity flex)  *(~1–2 wk)*
**Goal:** the hard gate exists before any collection code. #1 credibility signal for a military audience.

| Task | DoD |
|---|---|
| 1.1 Pydantic schemas: `RoE`, `SentinelState`, `Subject`, `AuthContext` | Validation tests pass on valid + invalid RoE |
| 1.2 Scope & Authorization Engine: `assert_allows(classification, source_category, subject)` | Disallowed source/out-of-scope subject **raises** — proven by test |
| 1.3 Tool Abstraction Layer: `IntelTool` ABC (rate-limit + cache + audit) | A dummy tool passes all three layers; audit rows appear |
| 1.4 FastAPI `POST /jobs` + `GET /jobs/{id}` + Postgres persistence | A job (subject+RoE) is stored and retrievable |

**Tag:** `v0.2-authz` · **Demo:** "Watch it refuse a disallowed source. That's by design." (Scores big with Army judges.)

### PHASE 2 — Passive Collection (the eyes open)  *(~1–2 wk)*
**Goal:** real OSINT on a subject you're authorized for (your own domain / a public region).

| Task | DoD |
|---|---|
| 2.1 OSINT Agent: WHOIS/RDAP, DNS, crt.sh, subdomains, email patterns | `POST /jobs` returns real entities for your own domain |
| 2.2 Geo-Event Agent: query your GTD/GDELT corpus for region+timeframe | Returns instability + modality + target context (your model's home turf) |
| 2.3 Threat-Intel Agent: VT/OTX/AbuseIPDB + NVD/OSV | Reputation + known-CVE references appear |
| 2.4 Everything routes through the Tool Abstraction Layer | Repeat request = cache hit; audit log proves it |

**Tag:** `v0.3-collection` · **Demo:** "Point it at our domain / a region — findings in seconds, rate-limited and logged."

### PHASE 3 — Intelligence Knowledge Graph (the centerpiece)  *(~1–2 wk)*
**Goal:** turn scattered findings into ONE queryable, visual model.

| Task | DoD |
|---|---|
| 3.1 Neo4j node/edge models (Part 5) | All core node/edge types writable |
| 3.2 Write collected findings into the graph | The Cypher query in Part 5.3 returns real results on your data |
| 3.3 Web/Infra Agent: passive fingerprint + Shodan/Censys | Tech stack + cloud/CDN/TLS on assets |
| 3.4 Deterministic risk-scoring engine (Part 4.4) | Reproducible per-entity score; unit-tested sub-scores |

**Tag:** `v0.4-graph` · **Demo:** the risk-colored graph on screen — "red = look here first."

### PHASE 4 — The Brain Bridge (HORUS meets ARGUS)  *(~1–2 wk — heart of the merge)*
**Goal:** your fine-tuned model becomes the RAG-grounded Analysis Agent.

| Task | DoD |
|---|---|
| 4.1 RAG: load MITRE ATT&CK (TA0043/TA0042) + geo corpus into ChromaDB | Semantic query returns a relevant technique/context |
| 4.2 `horus_brain/horus_provider.py`: wrap the Ollama model as a provider | Returns a structured report card from a subgraph |
| 4.3 Analysis Agent: subgraph + RAG context → HORUS model → findings | One real finding: context → evidence → framework mapping → recommendation → score |
| 4.4 Bounded LLM adjustment (±1 band, logged) | Model can't move a score >1 band; reason logged |
| 4.5 Human-validation checkpoint (Validate/Flag/Edit) | A report can't be FINAL without an analyst action recorded |

**Tag:** `v0.5-brain` · **Demo:** "The same brain that assessed geopolitics now reads the graph and writes the report — self-hosted, nothing leaves our infrastructure — and an analyst signs it off."

### PHASE 5 — Orchestration + Reporting (one command → one deliverable)  *(~1–2 wk)*
| Task | DoD |
|---|---|
| 5.1 LangGraph wiring of all agents (Part 2.3) | `build_sentinel_graph()` runs end-to-end |
| 5.2 Redis queue + async workers + Postgres checkpointing | A job resumes after a mid-run kill |
| 5.3 Reporting Agent: Jinja2 → WeasyPrint PDF + HTML + JSON (Part 6) | One job → full 9-section report |
| 5.4 Chain-of-custody appendix (RoE + timestamps + validation record) | Report proves what ran, when, under what authorization, validated by whom |

**Tag:** `v0.6-report` · **Demo:** "One subject in, one full intelligence report out, in minutes."

### PHASE 6 — The Unified UI (what judges actually click)  *(~1–2 wk — CRITICAL)*
**Goal:** a polished HORUS Command Center where judges try it themselves, zero setup.

| Task | DoD |
|---|---|
| 6.1 Evolve your SPA into a mode selector: **Geo-Intel | OSINT-Recon** | Clean HORUS home, two clear buttons |
| 6.2 Geo-Intel view = your existing chat, preserved | Unchanged, still great |
| 6.3 Recon view: subject + generate demo RoE → live job progress → report | Judge submits a subject, watches agents run, gets a report |
| 6.4 Embed the interactive Cytoscape graph | Judge pans/zooms, clicks a node, sees its risk |
| 6.5 "Command Center" military-grade visual polish | Looks like a real ops console |
| 6.6 **Guided Demo** button (pre-authorized safe subject, one click) | A judge runs a full assessment with zero setup |

**Tag:** `v0.7-ui` · **Demo:** hand a judge the laptop → "Run Guided Demo" → they watch HORUS work. This moment moves you to the podium.

### PHASE 7 — Polish, Hardening, Deploy  *(~1 wk)*
| Task | DoD |
|---|---|
| 7.1 Test suite + GitHub Actions CI (lint, mypy, test, bandit/pip-audit) | Green pipeline on every push |
| 7.2 Observability: structured logs + a simple metrics view | Job count + duration visible |
| 7.3 Deploy full stack (extend existing Terraform) | Live URL judges can reach |
| 7.4 Security review pass (secrets management, input validation, no ToS breaches) | Documented review checklist, all green |

**Tag:** `v0.8-prod`

### PHASE 8 — The Pitch (engineered to win)  *(~3–4 days)*
| Task | DoD |
|---|---|
| 8.1 3-minute demo video: problem → live dual-mode demo → architecture | Uploaded, tight, no dead air |
| 8.2 Update whitepaper/README to the unified HORUS Sentinel story | One coherent document |
| 8.3 Slide deck (10–12 slides) mapping features → judging criteria | Rehearsed under time |
| 8.4 Viva dry-run: every member answers auth, graph, model, scoring, ethics | All three fluent on all four |

**Tag:** `v1.0-competition`

---

## PART 10 — Why This Wins (Feature → Judging Advantage)

| Judge cares about | Your feature | Why competitors likely lack it |
|---|---|---|
| Real, working software | Two deployed modes + a model you actually fine-tuned | Most bring a prototype/slides |
| Technical depth | Multi-agent LangGraph + knowledge graph + RAG + self-hosted fine-tuned brain | Rare to have all four in one |
| Responsibility (military!) | Authorization engine + passive-only + human validation | Most ignore authorization entirely |
| Data sovereignty | Self-hosted model — nothing leaves the infrastructure | Most call a cloud API |
| Cost engineering | Your $4.85 FinOps + free-tier fine-tuning story | Distinctive, memorable |
| Hands-on trust | Judges run the Guided Demo themselves | A live demo beats any slide |
| A story they remember | "ARGUS's hundred eyes feed the Eye of HORUS" | Most have no narrative |
| Visual impact | The risk-colored knowledge graph | Single most screenshot-worthy artifact |
| Honesty / rigor | Human-in-the-loop reflecting the model's real limits | Signals maturity, not weakness |

---

## PART 11 — Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Breaking the winning project during the merge | Medium | High | Freeze `horus-geointel/`; build around it |
| Scope creep (trying to build all of ARGUS perfectly) | High | High | Phases 0–4 + 8 are the minimum winning system; the rest is polish |
| Free-tier rate limits/quotas (Shodan/Censys/VT) stall mid-phase | Medium | Medium | Cache hard from Phase 1; use fixtures in tests |
| LLM iteration cost creeps up | Low | Low | Self-hosted model = ~$0 marginal; that's the point |
| Neo4j/WeasyPrint technical friction | Medium | Low | Half-day spike budget if needed |
| Judges can't run the demo (setup friction) | Medium | High | Phase 6.6 Guided Demo + pre-authorized safe subject |
| The "model can't do security" question in the viva | Medium | High | Path C + human validation answers it head-on; rehearse the answer |
| 3-people waterfall — one blocker stalls all | Medium | Medium | Short phases + clear DoD; timebox blockers, move on, return |
| Docs drift from code | Medium | Low | Update README at the end of each phase, not just at the finish |

---

## PART 12 — The Minimum Winning System (if time gets tight)

**Must-have (Phases 0–4 + 6 + 8):**
- ✅ Winning geo-intel mode, preserved
- ✅ Authorization engine (the ethics flex)
- ✅ Passive OSINT + geo-event + one enrichment source
- ✅ The knowledge graph, visualized
- ✅ Your fine-tuned model as the RAG-grounded reasoning brain + human validation
- ✅ A unified UI with both modes + a Guided Demo
- ✅ A rehearsed 3-minute video + viva

Even this is a **dual-mode, multi-agent, self-hosted-AI, authorization-gated, human-validated intelligence platform with a fine-tuned model at its core** — vastly beyond a #20 project.

---

## PART 13 — Answering the Hard Viva Questions (rehearse these)

**Q: "Your model was trained on 2020 terrorism data. How can it do cyber recon?"**
A: "It doesn't do cyber exploitation. It's the *reasoning and reporting* layer. The specialized agents collect current OSINT and build a knowledge graph; the model's trained skill — turning correlated intelligence into a structured, prioritized report — is exactly what we use, grounded by RAG so it reasons over *retrieved current facts*, not its training memory. And a human analyst validates every report before it's final."

**Q: "Is this an attack tool?"**
A: "No — it's passive and defensive by design. It only consumes already-public data and never touches third-party infrastructure. There's a hard authorization gate, and it stops at *recommendation*. It's a blue-team analyst tool: the same lens an adversary would use, turned around so a defender sees their own exposure first."

**Q: "Why should we trust the AI's output?"**
A: "You shouldn't trust it blindly — and we designed for that. The risk score is deterministic and reproducible; the model can only adjust it within one band and must log why. Every claim is traceable to a source and timestamp. And a human analyst signs off before anything is final. AI-augmented, human-authoritative."

**Q: "What's genuinely novel here?"**
A: "Three things together: a multi-agent OSINT swarm that builds a *queryable intelligence graph*; a *self-hosted, fine-tuned* domain model as the reasoning core (data sovereignty on a $5 budget); and authorization + chain-of-custody + human validation as first-class features. Most projects have one of these. We integrated all three into a working system."

---

## PART 14 — Immediate Next Steps (start now)

1. As a team, lock the pitch (Part 0.2) until all three of you can say it in one breath.
2. Execute Phase 0.1 — create `horus-sentinel`, move the winning project in untouched, confirm it still runs.
3. Execute Phase 0.2 — `docker-compose` with the model serving locally via Ollama.
4. Come back and we'll write, together, the first real code:
   - `schemas/roe.py` + `core/authorization.py` (Phase 1)
   - `horus_brain/horus_provider.py` (the bridge)
   - the updated unified whitepaper

---

*HORUS Sentinel preserves the award-winning Horus-OSINT project completely, adds a passive multi-agent OSINT collection engine (ARGUS — "the many-eyed collection engine that feeds HORUS"), and unifies both under one brand, one self-hosted reasoning brain, and one Command Center — engineered specifically to move from rank #20 to a podium finish at ITC-Egypt Track 3, and kept scope-honest for a defensive military audience. This document is the technical and strategic source of truth for the build.*
