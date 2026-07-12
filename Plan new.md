# HORUS SENTINEL — Master Specification & Build Plan
## An Authorized Offensive-Reconnaissance & Intelligence Platform (Educational)
### v2.0 — Revised: Active Reconnaissance + Precision Web-Scraping Engine

> **Competition:** ITC-Egypt 2026 · Track 3 — Intelligent Software Systems · Air Defence College (Egyptian Military)
> **Project ID:** ITC-2026-T3-0726 · **Supervisor:** Sarah Mohammed Taha Khater
> **Team:** 3 members (Mahmoud, Mirna, Sondos) — waterfall, whole team on each task
> **Foundational asset:** the award-winning fine-tuned model `mahmoudalyosify/Horus-OSINT` (Llama-3-8B, QLoRA)
> **Goal:** move from rank #20 to a **1st / 2nd place** finish
>
> **This version's change (what you asked for):** the platform is now a **hands-on, offensive-reconnaissance intelligence tool for real educational use** — it performs **active reconnaissance on authorized/owned targets**, **precision web scraping of public sources**, deep OSINT research, and produces a **precise intelligence report**. Everything active is gated behind the Authorization Engine.

---

## PART 0 — THE CRITICAL FRAME (read this first — the competition weighs it heavily)

### 0.1 The one line that keeps this project winning instead of disqualified

There is a hard boundary between two things that look similar to outsiders but are completely different to a security professional (and to a military judge):

| ✅ What HORUS Sentinel IS | ❌ What it is NOT |
|---|---|
| **Authorized offensive reconnaissance** — active scanning of targets you **own** or have **written permission** for | Attacking systems you don't own / have no permission for |
| **Reconnaissance & intelligence** — discovery, enumeration, mapping, correlation, reporting | **Exploitation** — breaking in, delivering payloads, bypassing authentication |
| **Precision web scraping** of **public** data, respecting robots.txt + rate limits + law | Scraping behind logins/paywalls, harvesting personal data unlawfully, DoS-like hammering |
| A **red-team recon** and **CTI analyst** trainer | A weapon |

**The educational value is real and legitimate:** this is exactly how professional red teams, penetration testers, and intelligence analysts are trained — the *reconnaissance* phase of an authorized engagement. HORUS Sentinel teaches and automates that phase, produces a professional intelligence product from it, and **stops at the boundary of exploitation** — by design.

### 0.2 Why this framing is a *strength* in front of military judges (not a risk)

A military audience respects **discipline and rules of engagement** more than raw capability. A tool that says *"I can perform aggressive reconnaissance, but only under a signed authorization, only on in-scope targets, and I log every packet"* demonstrates exactly the operational maturity they train for. The **Scope & Authorization Engine** is therefore not a limitation to apologize for — it is the **centerpiece feature** that makes an offensive tool responsible. Lead your demo with it.

### 0.3 The MITRE ATT&CK anchor (gives you academic + professional credibility)

The whole platform maps cleanly to the **first two tactics** of the MITRE ATT&CK framework — the *pre-compromise* phase, which is precisely reconnaissance:

- **TA0043 — Reconnaissance** — active scanning (T1595), gathering victim host/network/identity information (T1592/T1590/T1589), searching open technical databases (T1596).
- **TA0042 — Resource Development** — what an adversary could stage from what they learned.

HORUS Sentinel operationalizes TA0043 for **authorized defenders and trainees**: it shows exactly what an adversary would discover in the recon phase, so a defender sees their own exposure first. That's the entire academic thesis of the project, and it's defensible in any viva.

### 0.4 The scope decision you made (drives the whole architecture)

You chose: **active reconnaissance on your own/authorized targets + precision scraping of public sources.** So the system has two collection intensities:

- **PASSIVE** (default, runs on anything in-scope): OSINT from public records + public web scraping.
- **ACTIVE** (gated, runs ONLY on owned/authorized targets in the RoE): port/service scanning, active enumeration, active fingerprinting.

The Authorization Engine is what separates them. No active operation ever runs without an RoE that explicitly authorizes active scanning **and** lists the target as owned/in-scope.

### 0.5 The pitch (memorize it)

> **"HORUS Sentinel is an autonomous offensive-reconnaissance analyst. Under a signed authorization, its ARGUS agents perform active reconnaissance on in-scope targets and precision-scrape public intelligence, correlate everything into a live attack-surface graph, and our self-hosted fine-tuned model — the Eye of HORUS — reasons over it to produce a precise, evidence-backed intelligence report. It performs the full reconnaissance phase of a professional engagement, and stops exactly where exploitation would begin."**

---

## PART 1 — The Problem, The Users, The Educational Value

### 1.1 The real problem
The reconnaissance phase of any security assessment or intelligence task is **manual, slow, and fragmented**. A red-teamer or analyst juggles a dozen CLI tools and browser tabs, then hand-assembles findings. Trainees have no single, safe, auditable environment to *learn* professional recon end-to-end and produce a real deliverable from it.

### 1.2 What HORUS Sentinel does
Given an **authorized target** + a signed **RoE**, it autonomously:
1. **Reconnoiters** — passive OSINT + (if authorized) active scanning/enumeration.
2. **Scrapes** — precision, compliant extraction from public web sources for intelligence.
3. **Correlates** — every finding into a unified **Attack-Surface / Intelligence Graph**.
4. **Enriches** — reputation, known-CVE correlation, ATT&CK technique mapping.
5. **Reasons** — the fine-tuned HORUS model (RAG-grounded) prioritizes and explains.
6. **Reports** — a precise, chain-of-custody intelligence report (PDF/HTML/JSON).
7. **Validates** — a human analyst signs off before the report is final.

### 1.3 Users
| User | Use case |
|---|---|
| **Red-team / pentest trainee** | Learn + automate the authorized recon phase end-to-end |
| **Intelligence / CTI analyst** | Deep OSINT research → structured intelligence product |
| **SOC / blue team** | See own external exposure exactly as an adversary would |
| **Instructor (Air Defence College)** | A safe, auditable, teachable recon+intel platform for cadets |

### 1.4 The educational thesis (state this explicitly in the report & viva)
*"Reconnaissance is the first ATT&CK tactic and the foundation of both offense and defense. HORUS Sentinel is a training and automation platform for the authorized reconnaissance phase: it demonstrates, safely and under strict rules of engagement, exactly what can be discovered about a target from active scanning and public sources — turning that into a professional intelligence report — so that trainees learn the tradecraft and defenders understand their exposure."*

---

## PART 2 — System Architecture

### 2.1 The four planes

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HORUS SENTINEL                              │
│                                                                     │
│  ┌───────────────────────── CONTROL PLANE ──────────────────────┐   │
│  │  Scope & Authorization Engine  (RoE · scope · active gate)   │   │
│  │  Orchestrator (LangGraph stateful, checkpointed)             │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                 authorized job (passive and/or active)               │
│  ┌───────────────── COLLECTION PLANE ("ARGUS eyes") ─────────────┐   │
│  │  PASSIVE:  OSINT Agent · Web-Scraping Agent · Geo-Event Agent │   │
│  │  ACTIVE:   Network Recon Agent (gated) · Active Fingerprint   │   │
│  │  Threat-Intel Enrichment Agent                                │   │
│  │  → all via Tool Abstraction Layer                             │   │
│  │    (classification-checked · rate-limited · cached · audited) │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                        normalized findings                           │
│  ┌───────────────────── KNOWLEDGE PLANE ────────────────────────┐   │
│  │  PostgreSQL · Neo4j (Attack-Surface/Intel Graph) ·           │   │
│  │  ChromaDB (RAG: ATT&CK + corpus) · Redis · Evidence store    │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                     graph + retrieved context                        │
│  ┌────────────────── REASONING & DELIVERY PLANE ────────────────┐   │
│  │  HORUS Brain (self-hosted fine-tuned Llama-3) →              │   │
│  │  Analysis Agent (RAG) → deterministic risk scoring →         │   │
│  │  Human validation → Reporting Agent → PDF / HTML / JSON      │   │
│  └───────────────────────────────────────────────────────────────┘  │
│                    HORUS Command Center (Unified Web UI)             │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Design invariants (never violate — this is what "production-grade + responsible" means)

1. **Passive by default; active by explicit exception.** Active operations run **only** when the RoE has `active_scanning_authorized = true` **and** the target is in `owned_in_scope`.
2. **No external call bypasses the Tool Abstraction Layer.** Classification check + rate-limit + cache + audit are enforced centrally.
3. **No job runs without a valid, signed RoE.** The Authorization Engine is a hard gate.
4. **Scraping is compliant by construction** — robots.txt honored, transparent User-Agent with contact, conservative delays, exponential backoff on 429/503, no auth/paywall bypass, no unlawful personal-data collection. (See Part 4.)
5. **Deterministic risk score; the LLM explains, never invents.** Bounded ±1 band, logged.
6. **Full chain of custody** — every finding traceable to a source + timestamp; every active action logged (target, port, time, authorization ID).
7. **Human-authoritative** — analyst validates before FINAL. The system **stops at recommendation**; it never exploits.

### 2.3 Orchestration (LangGraph) — with the active gate as a conditional edge

```python
# workflows/sentinel_graph.py  (skeleton)
from langgraph.graph import StateGraph, END
from schemas import SentinelState

def route_after_passive(state: SentinelState) -> str:
    # THE ACTIVE GATE: only branch to active recon if RoE explicitly allows it.
    if state.roe.active_scanning_authorized and state.target_is_owned_in_scope:
        return "network_recon"
    return "threat_intel"          # skip active entirely otherwise

def build_sentinel_graph():
    g = StateGraph(SentinelState)
    g.add_node("authorize",     authorization_gate)
    g.add_node("osint",         osint_agent)            # passive
    g.add_node("web_scrape",    web_scraping_agent)     # passive, compliant
    g.add_node("geo_event",     geo_event_agent)        # passive (your GTD/GDELT strength)
    g.add_node("network_recon", network_recon_agent)    # ACTIVE — gated
    g.add_node("threat_intel",  threat_intel_agent)
    g.add_node("analysis",      analysis_agent)          # HORUS brain + RAG
    g.add_node("validate",      human_validation_gate)
    g.add_node("report",        reporting_agent)

    g.set_entry_point("authorize")
    g.add_edge("authorize", "osint")
    g.add_edge("osint", "web_scrape")
    g.add_edge("web_scrape", "geo_event")
    g.add_conditional_edges("geo_event", route_after_passive,
                            {"network_recon": "network_recon", "threat_intel": "threat_intel"})
    g.add_edge("network_recon", "threat_intel")
    g.add_edge("threat_intel", "analysis")
    g.add_edge("analysis", "validate")
    g.add_edge("validate", "report")
    g.add_edge("report", END)
    return g.compile(checkpointer=postgres_checkpointer)
```

### 2.4 Tool Abstraction Layer — now enforces the passive/active classification

```python
class ReconTool(ABC):
    name: str
    classification: Literal["passive", "active"]   # active tools are gated here
    source_category: str
    rate_limit: RateBudget
    cache_ttl: int

    @abstractmethod
    async def run(self, target: Target, ctx: AuthContext) -> ToolResult: ...

    async def __call__(self, target, ctx):
        # HARD GATE — active tools cannot execute without explicit authorization + ownership.
        ctx.assert_allows(self.classification, self.source_category, target)
        if self.classification == "passive" and (cached := await cache.get(self.cache_key(target))):
            return cached
        await self.rate_limit.acquire()
        result = await self.run(target, ctx)
        await audit_log.record(self.name, self.classification, target, ctx, result.summary())
        if self.classification == "passive":
            await cache.set(self.cache_key(target), result, ttl=self.cache_ttl)
        return result
```

---

## PART 3 — The Agents (Collection Plane in detail)

### 3.1 OSINT Collection Agent — PASSIVE
WHOIS/RDAP, DNS (all record types), certificate transparency (crt.sh), passive subdomain discovery, email-pattern inference, breach-corpus lookups (reputable APIs), public code-repo metadata. → base entity picture.

### 3.2 Web-Scraping Agent — PASSIVE, PRECISION, COMPLIANT  *(new — a headline feature)*
See Part 4 for the full engine. Extracts structured intelligence from **public** web sources: target-relevant pages, public directories, news, public technical databases, social/company public profiles. Every fetch honors robots.txt, rate limits, and law; every extraction is stored with source + timestamp for chain of custody.

### 3.3 Geo-Event Context Agent — PASSIVE  *(your existing strength)*
Queries your GTD/GDELT-derived corpus (the 159,826-pair dataset) + optional live news APIs → geopolitical/threat-event context for a region/entity/timeframe. Prime RAG material for the HORUS brain.

### 3.4 Network Reconnaissance Agent — **ACTIVE (GATED)**  *(the offensive capability)*
**Runs only on owned/authorized targets when the RoE authorizes active scanning.**
- Port & service discovery (e.g., Nmap wrapped as an `active` ReconTool).
- Active service/version enumeration and banner grabbing.
- Active web-tech fingerprinting (direct requests to the target).
- Respects a strict **rate budget** and **timing profile** even when active.
- **Absolute stop line:** discovery/enumeration only. **No exploitation, no auth attempts, no brute force, no payloads.** If a feature would cross into exploitation, it is not built — the discovery/defensive alternative is documented instead.

### 3.5 Threat-Intelligence Enrichment Agent — PASSIVE
VirusTotal / OTX / AbuseIPDB (reputation), NVD/OSV (known-CVE correlation for discovered product+version — informational), MITRE ATT&CK technique mapping (TA0043/TA0042 emphasis).

---

## PART 4 — The Precision Web-Scraping Engine (full spec — the competition cares about this)

This is a distinguishing feature, so it's specified in depth. The engine is **precise** (structured, targeted extraction — not a blind crawler) and **compliant by construction**.

### 4.1 Architecture
```
tools/scraping/
├── fetcher.py        # compliant HTTP client (headers, timeouts, retries)
├── robots.py         # robots.txt fetch + parse + cache + can_fetch()
├── throttle.py       # per-domain adaptive rate limiter (crawl-delay aware)
├── extractor.py      # structured extraction (CSS/XPath/JSON-LD + optional LLM parse)
├── normalizer.py     # → typed Finding objects with provenance
└── evidence.py       # store raw response + hash + timestamp (chain of custody)
```

### 4.2 Compliance rules baked into the engine (each is a code-level control, not a guideline)
1. **robots.txt first.** Fetch and cache `domain/robots.txt`; call `can_fetch(user_agent, url)` before **every** request. If disallowed → skip and log the skip. This is enforced in `fetcher.py`, so no scraping code can bypass it.
2. **Transparent identity.** A stable, honest `User-Agent` that identifies the project + a contact URL. No pretending to be a browser to evade detection.
3. **Conservative, adaptive rate limiting.** Default a deliberate per-domain delay; honor `Crawl-delay` when present; adapt to server latency. Never behave like a DoS.
4. **Exponential backoff with jitter** on HTTP 429/503. On repeated errors, a **circuit breaker** pauses that domain.
5. **Public data only.** No login/paywall/access-control circumvention (that boundary is where lawful public scraping ends). No collection behind authentication.
6. **Data minimization.** Extract only fields the intelligence task needs; avoid unnecessary personal data; where personal data is incidental, minimize/redact per data-protection norms.
7. **Provenance & audit.** Store the raw response + a content hash + timestamp + the robots decision, so every scraped datum is defensible and traceable.

> **Viva-ready line:** *"Our scraper is compliant by construction: robots.txt is checked in the fetch layer before every request, we identify ourselves transparently, we rate-limit adaptively and back off on errors, we only touch public data, and we keep provenance on everything. Those aren't policies bolted on top — they're controls in the code that no agent can bypass."*

### 4.3 Precision (not a blind crawler)
- **Targeted seeds** from the job's subject/target (not "crawl the whole web").
- **Structured extraction** via CSS/XPath/JSON-LD selectors per source type; optional LLM-assisted parsing to turn messy HTML into typed fields.
- **Deduplication** against the graph (don't re-store known entities).
- **Typed output** — every scraped item becomes a normalized `Finding` written to the Knowledge Plane with its provenance.

### 4.4 Suggested libraries
`httpx` (async fetch), `urllib.robotparser` / `protego` (robots), `selectolax` or `beautifulsoup4` + `lxml` (parse), `tenacity` (backoff). For JS-heavy pages (only if needed), a headless browser (Playwright) behind the same compliance layer.

---

## PART 5 — The Reasoning Brain (your fine-tuned model, elevated)

### 5.1 Role
Your `Horus-OSINT` model already emits a **structured Intelligence Report Card**. Here it becomes the **Analysis Agent**, reasoning over a **correlated graph + RAG context** rather than a single prompt — a large capability jump on the same model.

### 5.2 RAG-grounded reasoning
1. Retrieve the target's **subgraph** (entity + 1–2 hop neighborhood) from Neo4j.
2. Retrieve grounding from ChromaDB: relevant **MITRE ATT&CK** techniques + (for geo subjects) the threat corpus.
3. Structured prompt: correlated facts + framework context → report-card sections.
4. Ground truth stays in the graph; the model synthesizes and explains, referencing evidence IDs — it does not invent entities.

### 5.3 The provider bridge (one clean integration point)
```python
# horus_brain/horus_provider.py
class HorusReasoningProvider(LLMProvider):
    """Self-hosted fine-tuned Llama-3 via Ollama (VPC-internal). Graph-grounded."""
    name = "horus-selfhosted"; endpoint = "http://ollama:11434/api/generate"; model = "horus-osint"
    async def reason(self, subgraph, rag_context) -> ReportCard:
        return ReportCard.parse(await self._call_ollama(build_intel_prompt(subgraph, rag_context)))
```

### 5.4 Deterministic risk scoring
```
RiskScore(entity) = w_e·Exposure + w_t·ThreatContext + w_i·ReputationIntel + w_c·Criticality
defaults:           0.30           0.30              0.20                 0.20
```
Deterministic base score + band; model may adjust **±1 band max**, must log the reason, shown in the report. Reproducible.

### 5.5 Human-validation checkpoint
Before FINAL, an analyst sees draft findings + evidence → **Validate / Flag / Edit**. Honors the model card's guidance; matches real intelligence sign-off; a selling point ("AI-augmented, human-authoritative").

---

## PART 6 — Knowledge Model (Attack-Surface / Intelligence Graph)

**Nodes:** `Organization, Domain, Subdomain, IP, Service, Port, Technology, Certificate, Email, Person, CVE, CloudAsset, Region, ThreatActor, Event, Indicator, WebResource`.

**Edges (examples):**
```
(Organization)-[:OWNS]->(Domain)-[:HAS_SUBDOMAIN]->(Subdomain)-[:RESOLVES_TO]->(IP)
(IP)-[:EXPOSES]->(Port)-[:RUNS]->(Service)-[:IDENTIFIED_AS]->(Technology)-[:HAS_VULNERABILITY]->(CVE)
(WebResource)-[:MENTIONS]->(Person) ; (WebResource)-[:SCRAPED_FROM]->(Source)
(Region)-[:HAS_EVENT]->(Event)<-[:ASSOCIATED_WITH]-(ThreatActor)
```

**Why a graph (the strongest technical idea):** analysis becomes traversal, not manual cross-referencing; the Analysis Agent retrieves subgraphs as grounded context; the risk-colored graph is your **single most screenshot-worthy artifact**.

```cypher
// active-recon result: owned services exposing a critical known vuln
MATCH (i:IP)-[:EXPOSES]->(p:Port)-[:RUNS]->(s:Service)-[:IDENTIFIED_AS]->(t:Technology)-[:HAS_VULNERABILITY]->(c:CVE)
WHERE c.cvss >= 9.0
RETURN i.address, p.number, s.name, t.version, c.id, c.cvss ORDER BY c.cvss DESC
```

---

## PART 7 — Output System (the precise intelligence report)

### 7.1 Report structure (9 sections)
1. **Executive Summary** — model-authored, the picture + top findings + metrics.
2. **Target, Scope & Authorization** — the RoE, what was authorized (passive/active), sources enabled.
3. **Reconnaissance Findings** — passive OSINT + (if run) active scan results, each with source/timestamp.
4. **Web-Intelligence (Scraped)** — structured public-source findings with provenance.
5. **Enrichment** — reputation, known-CVE references, ATT&CK technique mapping.
6. **Attack-Surface / Intelligence Graph** — rendered map, risk-colored (interactive in HTML).
7. **Risk Analysis** — matrix + per-finding score with component breakdown.
8. **Prioritized Findings & Recommendations** — evidence → why it matters → ATT&CK mapping → recommendation.
9. **Appendix — Chain of Custody** — full evidence list (source + timestamp + robots decisions for scraped items), the RoE, active-action log, analyst validation record.

### 7.2 Formats
PDF (Jinja2 → WeasyPrint) · interactive HTML (with live graph) · JSON (machine-readable).

---

## PART 8 — Technology Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| API | FastAPI + Uvicorn |
| Orchestration | LangGraph (+ LangChain adapters) |
| LLM | Provider-abstracted; **default = self-hosted fine-tuned Llama-3 via Ollama** |
| Active recon | Nmap (wrapped as gated `active` ReconTool), async enumeration |
| Web scraping | httpx + protego/urllib.robotparser + selectolax/bs4+lxml + tenacity (+ Playwright only if needed) |
| OSINT | WHOIS/RDAP, dnspython, crt.sh, Shodan, Censys |
| Threat intel | VirusTotal, OTX, AbuseIPDB, NVD/OSV, MITRE ATT&CK |
| Relational | PostgreSQL |
| Graph | Neo4j (prod) / networkx (MVP) |
| Vector | ChromaDB |
| Cache/queue | Redis |
| Evidence store | MinIO / S3 |
| Reporting | Jinja2 + WeasyPrint; Cytoscape.js/D3 |
| Frontend | React + Tailwind + Cytoscape.js |
| Deploy | Docker + docker-compose → AWS (extend existing Terraform) |
| Observability | structlog + Prometheus/Grafana |
| CI/CD | GitHub Actions (ruff, mypy, pytest, bandit, pip-audit) |

---

## PART 9 — Repository Structure

```
horus-sentinel/
├── horus-geointel/            # THE WINNING PROJECT — moved in whole, FROZEN
├── api/                       # FastAPI app + routes
├── core/
│   ├── authorization.py       # Scope & Authorization Engine + RoE (passive/active gate)
│   ├── audit.py               # chain-of-custody (incl. active-action + robots logs)
│   └── rate_limit.py          # token-bucket rate budgets
├── agents/
│   ├── osint_agent.py         # passive
│   ├── web_scraping_agent.py  # passive, compliant  ← new
│   ├── geo_event_agent.py     # passive (your strength)
│   ├── network_recon_agent.py # ACTIVE — gated       ← new
│   ├── threat_intel_agent.py  # passive
│   ├── analysis_agent.py      # RAG-grounded reasoning
│   └── report_agent.py
├── tools/
│   ├── base.py                # ReconTool ABC (classification gate + rate-limit/cache/audit)
│   ├── whois_tool.py · dns_tool.py · crtsh_tool.py
│   ├── shodan_tool.py · censys_tool.py
│   ├── nmap_tool.py           # ACTIVE — gated       ← new
│   ├── threatintel_tool.py
│   └── scraping/              # the precision scraping engine (Part 4)
│       ├── fetcher.py · robots.py · throttle.py
│       ├── extractor.py · normalizer.py · evidence.py
├── graph/                     # Attack-Surface/Intel Graph models + queries
├── scoring/                   # deterministic risk-scoring engine
├── rag/                       # ATT&CK + geo corpus embeddings + retrieval
├── horus_brain/horus_provider.py   # bridge to the self-hosted model
├── workflows/sentinel_graph.py     # LangGraph (with active gate)
├── reporting/                 # Jinja2 → PDF/HTML/JSON
├── schemas/                   # SentinelState, RoE, Target, findings
├── horus-ui/                  # React + Cytoscape Command Center
├── deploy/                    # docker-compose, IaC
└── tests/
```

> **Team rule:** `horus-geointel/` is **frozen**. Build around it.

---

## PART 10 — Ground-Up Build Plan (Waterfall, 3 People Together)

Single ordered backlog. Rotate **Driver / Navigator / Verifier** per task so all three can answer anything in the viva. Each phase ends with a demoable result + a git tag. Phases 0–5 + 8 = **minimum winning system**; 6–7 = depth/polish. Pace: ~2 weeks/phase comfortable, ~1 week aggressive.

### PHASE 0 — Consolidation & Setup  *(~2–3 days)*
| Task | DoD |
|---|---|
| 0.1 Monorepo; move winning project into `horus-geointel/` untouched | Old project still runs as a subfolder |
| 0.2 `docker-compose` (Postgres, Neo4j, Redis, ChromaDB, MinIO, Ollama serving your model) | `docker-compose up` runs all; Ollama returns a report card |
| 0.3 Top-level README + architecture diagram + pitch | README tells the ARGUS-feeds-HORUS story |
**Tag:** `v0.1-foundation`

### PHASE 1 — Control Plane (Authorization + the passive/active gate)  *(~1–2 wk)*  ← **your biggest flex**
| Task | DoD |
|---|---|
| 1.1 Schemas: `RoE` (with `active_scanning_authorized`, `owned_in_scope`), `SentinelState`, `Target`, `AuthContext` | Validation tests pass on valid + invalid RoE |
| 1.2 Authorization Engine: `assert_allows(classification, source_category, target)` | **Active op without authorization / on out-of-scope target → raises**, proven by test |
| 1.3 Tool Abstraction Layer: `ReconTool` ABC (classification gate + rate-limit + cache + audit) | A dummy `active` tool refuses without authorization; a `passive` tool passes; audit rows appear |
| 1.4 FastAPI `POST /jobs` + Postgres persistence | Job (target+RoE) stored & retrievable |
**Tag:** `v0.2-authz` · **Demo:** "Watch it refuse an active scan without authorization. That's by design."

### PHASE 2 — Passive Collection + Precision Scraping  *(~2 wk)*
| Task | DoD |
|---|---|
| 2.1 OSINT Agent (WHOIS/RDAP, DNS, crt.sh, subdomains, email patterns) | Real entities for your own domain |
| 2.2 **Scraping engine** (`fetcher`+`robots`+`throttle`+`extractor`+`normalizer`+`evidence`) | Scrapes a permitted public source; **robots-disallowed URL is skipped + logged**; provenance stored |
| 2.3 Web-Scraping Agent wraps the engine into the pipeline | Structured findings written to the graph with source+timestamp |
| 2.4 Geo-Event Agent over your GTD/GDELT corpus | Region/timeframe context returned |
| 2.5 Everything routes through the Tool Abstraction Layer | Repeat passive request = cache hit; audit proves it |
**Tag:** `v0.3-collection` · **Demo:** compliant scraping — "it checks robots.txt before every request and logs what it skipped."

### PHASE 3 — Active Reconnaissance (GATED)  *(~1–2 wk)*  ← **the offensive capability, done responsibly**
| Task | DoD |
|---|---|
| 3.1 `nmap_tool.py` as an `active` ReconTool — `assert_allows("active", ...)` **before** any execution | Test proves the gate check happens *before* any scan runs; unauthorized → raises, no scan |
| 3.2 Network Recon Agent: passive results always; active **only** when authorized + in-scope | With `active=false`: zero scan; with `active=true` on your domain: real ports/services |
| 3.3 Active enumeration + banner grabbing (discovery only — hard stop before exploitation) | Service/version data on your own target; documented "no exploitation" boundary |
| 3.4 Active-action audit log (target, port, time, authorization ID) | Every active action is logged for chain of custody |
**Tag:** `v0.4-active` · **Demo:** on YOUR OWN domain, under an RoE you generated — full active recon, every packet logged.

### PHASE 4 — Graph + Risk Scoring  *(~1–2 wk)*
| Task | DoD |
|---|---|
| 4.1 Neo4j node/edge models (Part 6) | All core types writable |
| 4.2 Write passive + scraped + active findings into the graph | The Cypher query in Part 6 returns real results |
| 4.3 Deterministic risk-scoring engine | Reproducible per-entity score; unit-tested sub-scores |
**Tag:** `v0.5-graph` · **Demo:** the risk-colored attack-surface graph.

### PHASE 5 — The Brain + Reporting  *(~2 wk)*
| Task | DoD |
|---|---|
| 5.1 RAG: MITRE ATT&CK (TA0043/TA0042) + geo corpus into ChromaDB | Semantic query returns relevant technique |
| 5.2 `horus_provider.py` bridge | Returns a report card from a subgraph |
| 5.3 Analysis Agent: subgraph + RAG → HORUS model → findings | One real finding: evidence → ATT&CK mapping → recommendation → score |
| 5.4 Bounded ±1 band + human-validation checkpoint | Score can't move >1 band; report can't be FINAL without analyst action |
| 5.5 Reporting Agent: Jinja2 → PDF + HTML + JSON (Part 7) | One job → full 9-section report with chain of custody |
**Tag:** `v0.6-report` · **Demo:** "One authorized target in → one precise intelligence report out."

### PHASE 6 — Orchestration end-to-end  *(~1 wk)*
| Task | DoD |
|---|---|
| 6.1 LangGraph wiring incl. the active conditional edge | `build_sentinel_graph()` runs end-to-end; RoE routes passive vs active |
| 6.2 Redis queue + async workers + Postgres checkpointing | Job resumes after a mid-run kill |
**Tag:** `v0.7-orchestration`

### PHASE 7 — The Unified UI (what judges click)  *(~2 wk — CRITICAL)*
| Task | DoD |
|---|---|
| 7.1 SPA mode selector: **Geo-Intel | Recon** | Clean HORUS home |
| 7.2 Geo-Intel view = your existing chat, preserved | Unchanged |
| 7.3 Recon view: target + generate RoE (toggle active) → live job → report | Judge submits, watches agents run, gets a report |
| 7.4 Interactive Cytoscape graph | Judge pans/zooms, clicks a node, sees risk |
| 7.5 "Command Center" military-grade polish | Looks like a real ops console |
| 7.6 **Guided Demo** button (pre-authorized safe target, one click) | Judge runs a full assessment with zero setup |
**Tag:** `v0.8-ui`

### PHASE 8 — Hardening, Deploy & Pitch  *(~1 wk)*
| Task | DoD |
|---|---|
| 8.1 Tests + GitHub Actions CI (lint, mypy, bandit, pip-audit) | Green pipeline |
| 8.2 Security & compliance review (secrets, scraping compliance, active-scope enforcement) | Documented checklist, all green |
| 8.3 Deploy full stack (extend Terraform) | Live URL |
| 8.4 3-min demo video + slides + viva dry-run | All three fluent on auth, scraping compliance, active scope, model, scoring, ethics |
**Tag:** `v1.0-competition`

---

## PART 11 — Why This Wins (Feature → Judging Advantage)

| Judge cares about | Your feature | Why competitors lack it |
|---|---|---|
| Real, working, *capable* software | Active recon + precision scraping + fine-tuned brain, all live | Most bring passive demos or slides |
| Technical depth | Multi-agent + graph + RAG + self-hosted model + compliant scraper | Rare to have all in one |
| **Discipline / RoE (military!)** | Authorization engine gating active ops; every packet logged | Most offensive demos ignore authorization |
| Legal/ethical maturity | Compliance-by-construction scraper (robots/rate/law) | Most scrapers are "smash and grab" |
| Data sovereignty | Self-hosted model — nothing leaves the infrastructure | Most call a cloud API |
| Hands-on trust | Judges run the Guided Demo themselves | A live demo beats any slide |
| A story they remember | "ARGUS's hundred eyes feed the Eye of HORUS" | Most have no narrative |
| Visual impact | Risk-colored attack-surface graph | Single most screenshot-worthy artifact |
| Academic anchor | Operationalizes MITRE ATT&CK TA0043 for authorized recon | Shows framework fluency |

---

## PART 12 — Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Active recon perceived as "attack tool"** | Medium | **High** | Part 0 framing; active only on owned/authorized targets; hard stop before exploitation; lead the demo with the authorization gate |
| Scraping compliance challenged in viva | Medium | Medium | Compliance-by-construction (Part 4); rehearse the Part 4.2 answer; show the robots-skip log live |
| Breaking the winning project | Medium | High | Freeze `horus-geointel/` |
| Scope creep | High | High | Phases 0–5 + 8 = minimum winning system |
| Free-tier rate limits stall a phase | Medium | Medium | Cache hard from Phase 1; fixtures in tests |
| Active scanning legal/scope mistake | Low | High | Engine refuses active on anything not in `owned_in_scope`; demo only on your own domain |
| Nmap/WeasyPrint/Neo4j friction | Medium | Low | Half-day spike budget |
| 3-people waterfall blocker stalls all | Medium | Medium | Short phases, clear DoD, timebox + move on |

---

## PART 13 — Hard Viva Questions (rehearse — this is where you win or lose)

**Q: "Isn't this an attack tool?"**
A: "No. It performs the *reconnaissance* phase of a professional engagement and stops exactly where exploitation begins — no auth attempts, no payloads, no exploitation code exists in it. Active scanning runs only on targets we own or are authorized for, enforced by the authorization engine, and every active action is logged. It's a red-team recon *trainer* and a defender's exposure tool."

**Q: "Your active scanner — what stops someone pointing it at a target they don't own?"**
A: "The engine itself. Active tools call the authorization check *before* executing, and it refuses unless the RoE explicitly authorizes active scanning *and* lists the target as owned/in-scope. There's a test that proves the check happens before any scan runs. In the demo we only ever scan our own domain under an RoE we generated."

**Q: "Is your web scraping legal?"**
A: "It's compliant by construction. The fetch layer checks robots.txt before every request, we identify ourselves transparently with contact info, we rate-limit adaptively and back off on errors so we never resemble a DoS, we only touch public data — never behind logins or paywalls — and we keep provenance on everything. Those are controls in the code, not policies on paper. Public-data scraping under these conditions is well-established as lawful."

**Q: "Your model was trained on 2020 geopolitical data — how does it do cyber recon?"**
A: "It doesn't exploit or scan — it *reasons and reports*. The agents gather current recon data and build a graph; the model's trained skill is turning correlated intelligence into a structured, prioritized report, grounded by RAG over the current graph and ATT&CK — not its training memory. And a human analyst validates every report."

**Q: "What's genuinely novel?"**
A: "An autonomous multi-agent system that runs the full authorized-reconnaissance phase — active scanning *and* compliant public-source scraping — correlates it into a queryable attack-surface graph, and uses a *self-hosted, fine-tuned* model as the reasoning core, with authorization + chain-of-custody + human validation as first-class features. Most projects have one piece; we integrated all of them, responsibly."

---

## PART 14 — Immediate Next Steps
1. Lock the Part 0 framing + the pitch until all three can say them cold. **This is your shield in the viva.**
2. Phase 0.1–0.2: monorepo, winning project frozen inside, model serving locally.
3. Come back and say **"ready for Phase 1"** — we write `schemas/roe.py` (with the active gate fields) + `core/authorization.py` together, since the passive/active gate is the spine of everything.

---

*HORUS Sentinel is an authorized offensive-reconnaissance and intelligence platform for real educational use. It performs active reconnaissance on owned/authorized targets and precision, compliant scraping of public sources, correlates findings into an attack-surface/intelligence graph, and uses the award-winning self-hosted fine-tuned model as its reasoning core to produce precise, chain-of-custody intelligence reports. It executes the full reconnaissance phase of a professional engagement — TA0043 — and stops, by design, exactly where exploitation would begin. This document is the technical and strategic source of truth for the build.*
