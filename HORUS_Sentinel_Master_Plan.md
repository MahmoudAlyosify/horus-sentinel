# HORUS SENTINEL — Master Specification & Build Plan
## An Authorized Offensive-Reconnaissance & Intelligence Platform (Educational)
### v3.0 — The Constitution (consolidated & authoritative)

> **Competition:** ITC-Egypt 2026 · Track 3 — Intelligent Software Systems · Air Defence College (Egyptian Military)
> **Project ID:** ITC-2026-T3-0726 · **Supervisor:** Sarah Mohammed Taha Khater
> **Team:** 3 members (Mahmoud, Mirna, Sondos) — waterfall, whole team on each task
> **Foundational asset:** the award-winning fine-tuned model `mahmoudalyosify/Horus-OSINT` (Llama-3-8B, QLoRA)
> **Goal:** move from rank #20 to a **1st / 2nd place** finish
>
> **This is the single source of truth.** It supersedes every earlier plan (v1.0 passive, v2.0 offensive).
> It records both the *strategy* and the *implemented reality* of HORUS Sentinel:
> an authorized offensive-reconnaissance & intelligence platform that performs active recon on
> owned/authorized targets, precision-scrapes public sources, correlates everything into an
> attack-surface graph, reasons over it with a **self-hosted or online fine-tuned model**, and
> produces a **precise bilingual (Arabic/English) intelligence report** — stopping, by design,
> exactly where exploitation would begin.

---

## PART 0 — THE CRITICAL FRAME (read this first — the competition weighs it heavily)

### 0.1 The one line that keeps this project winning instead of disqualified

There is a hard boundary between two things that look similar to outsiders but are completely
different to a security professional (and to a military judge):

| ✅ What HORUS Sentinel IS | ❌ What it is NOT |
|---|---|
| **Authorized offensive reconnaissance** — active scanning of targets you **own** or have **written permission** for | Attacking systems you don't own / have no permission for |
| **Reconnaissance & intelligence** — discovery, enumeration, mapping, correlation, reporting | **Exploitation** — breaking in, delivering payloads, bypassing authentication |
| **Precision web scraping** of **public** data, respecting robots.txt + rate limits + law | Scraping behind logins/paywalls, harvesting personal data unlawfully, DoS-like hammering |
| A **red-team recon** and **CTI analyst** trainer | A weapon |

The educational value is real and legitimate: this is exactly how professional red teams,
penetration testers, and intelligence analysts are trained — the *reconnaissance* phase of an
authorized engagement. HORUS Sentinel teaches and automates that phase, produces a professional
intelligence product from it, and **stops at the boundary of exploitation** — by design.

### 0.2 Why this framing is a *strength* in front of military judges

A military audience respects **discipline and rules of engagement** more than raw capability. A
tool that says *"I can perform aggressive reconnaissance, but only under a signed authorization,
only on in-scope targets, and I log every action"* demonstrates exactly the operational maturity
they train for. The **Scope & Authorization Engine** is therefore not a limitation to apologize
for — it is the **centerpiece feature** that makes an offensive tool responsible. Lead the demo
with it: *"Watch it refuse an active scan against a target we're not authorized for — 403, by design."*

### 0.3 The MITRE ATT&CK anchor (academic + professional credibility)

The platform maps cleanly to the **first two tactics** of MITRE ATT&CK — the *pre-compromise*
phase, which is precisely reconnaissance:

- **TA0043 — Reconnaissance** — active scanning (T1595), network service discovery (T1046),
  gathering victim host/network/identity info (T1592/T1590/T1589), external remote services
  (T1133), searching open technical databases (T1596).
- **TA0042 — Resource Development** / **TA0001 — Initial Access (T1190)** — what an adversary
  could stage/do *next* from what recon revealed (mapped as downstream risk; never performed).

HORUS Sentinel operationalizes TA0043 for **authorized defenders and trainees**: it shows exactly
what an adversary would discover in the recon phase, so a defender sees their own exposure first.

### 0.4 The two collection intensities (drives the whole architecture)

- **PASSIVE** (default, runs on anything in-scope): OSINT from public records + public web sources.
- **ACTIVE** (gated, runs ONLY on owned/authorized targets in the RoE): port/service scanning,
  active DNS/subdomain enumeration, active fingerprinting, and a compliant crawler/scraper.

The Authorization Engine separates them. **No active operation ever runs without an RoE that
explicitly authorizes active scanning (`active_authorized = true`) AND lists the target inside
`in_scope_domains`.** An out-of-scope active request is refused with **403** before it reaches
the collection plane.

### 0.5 Data sovereignty + language (added in this build)

- **Sovereign or online brain (pluggable).** The reasoning model runs either **self-hosted via
  Ollama** (nothing leaves the box — the right choice for an intelligence user) or **online via
  Hugging Face** (the analyst's token, collected at first run). One config switch; the report is
  identical either way.
- **Bilingual (Arabic / English).** The entire UI, the model's narrative, and the report switch
  between Arabic (RTL, default — it serves an Arabic-speaking intelligence audience) and English.

### 0.6 The pitch (memorize it)

> **"HORUS Sentinel is an autonomous offensive-reconnaissance analyst. Under a signed
> authorization, its ARGUS agents perform active reconnaissance on in-scope targets and
> precision-scrape public intelligence, correlate everything into a live attack-surface graph,
> and our fine-tuned model — the Eye of HORUS, self-hosted for full data sovereignty — reasons
> over it to produce a precise, evidence-backed intelligence report in Arabic or English. It
> performs the full reconnaissance phase of a professional engagement, and stops exactly where
> exploitation would begin."**

---

## PART 1 — The Problem, The Users, The Educational Value

### 1.1 The real problem
The reconnaissance phase of any security assessment or intelligence task is **manual, slow, and
fragmented**. A red-teamer or analyst juggles a dozen CLI tools and browser tabs, then
hand-assembles findings. Trainees have no single, safe, auditable environment to *learn*
professional recon end-to-end and produce a real deliverable from it.

### 1.2 What HORUS Sentinel does
Given an **authorized target** + a signed **RoE**, it autonomously:
1. **Reconnoiters** — passive OSINT + (if authorized) active scanning/enumeration.
2. **Scrapes** — precision, compliant extraction from public web sources.
3. **Correlates** — every finding into a unified **Attack-Surface / Intelligence Graph**.
4. **Enriches** — reputation, known-CVE correlation, ATT&CK technique mapping.
5. **Reasons** — the fine-tuned HORUS model (RAG-grounded) prioritizes and explains.
6. **Reports** — a precise, chain-of-custody intelligence report (PDF/HTML/JSON), Arabic or English.
7. **Validates** — a human analyst signs off before the report is final.

### 1.3 Users
| User | Use case |
|---|---|
| **Red-team / pentest trainee** | Learn + automate the authorized recon phase end-to-end |
| **Intelligence / CTI analyst** | Deep OSINT research → structured intelligence product |
| **SOC / blue team** | See own external exposure exactly as an adversary would |
| **Instructor (Air Defence College)** | A safe, auditable, teachable recon+intel platform for cadets |

### 1.4 The educational thesis (state it in the report & viva)
*"Reconnaissance is the first ATT&CK tactic and the foundation of both offense and defense. HORUS
Sentinel is a training and automation platform for the authorized reconnaissance phase: it
demonstrates, safely and under strict rules of engagement, exactly what can be discovered about a
target from active scanning and public sources — turning that into a professional intelligence
report — so trainees learn the tradecraft and defenders understand their exposure."*

---

## PART 2 — System Architecture

### 2.1 The four planes

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HORUS SENTINEL                              │
│  ┌───────────────────────── CONTROL PLANE ──────────────────────┐   │
│  │  Scope & Authorization Engine  (RoE · scope · ACTIVE gate)   │   │
│  │  Orchestrator (checkpointed stages; LangGraph-compatible)    │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                 authorized job (passive and/or active)               │
│  ┌───────────────── COLLECTION PLANE ("ARGUS eyes") ─────────────┐   │
│  │  PASSIVE:  OSINT · Web-Infra fingerprint · Geo-Event · TI     │   │
│  │  ACTIVE (gated): Network-Recon Agent — port scan + service    │   │
│  │            fingerprint · active DNS/subdomain enum · crawler  │   │
│  │  → all via the Tool Abstraction Layer                         │   │
│  │    (classification-checked · rate-limited · cached · audited) │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                        normalized findings                           │
│  ┌───────────────────── KNOWLEDGE PLANE ────────────────────────┐   │
│  │  PostgreSQL/SQLite · Neo4j/networkx (Attack-Surface Graph) ·  │   │
│  │  ChromaDB/keyword (RAG: ATT&CK + corpus) · Redis · Evidence   │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                     graph + retrieved context                        │
│  ┌────────────────── REASONING & DELIVERY PLANE ────────────────┐   │
│  │  HORUS Brain (fine-tuned Llama-3, self-hosted OR online HF) → │   │
│  │  Analysis Agent (RAG) → deterministic risk scoring →         │   │
│  │  Human validation → Reporting → PDF/HTML/JSON (AR/EN)         │   │
│  └───────────────────────────────────────────────────────────────┘  │
│                    HORUS Command Center (bilingual Web UI)           │
└─────────────────────────────────────────────────────────────────────┘
```

**Graceful degradation (implemented):** every heavy dependency is an optional accelerator with a
pure-Python fallback, so the platform runs with zero infrastructure and lights up when the real
services are present:

| Full stack (optional) | Fallback (always works) |
|---|---|
| PostgreSQL | SQLite file |
| Neo4j | in-process `networkx` graph |
| ChromaDB | deterministic keyword retriever |
| Ollama / HF online model | deterministic grounded synthesis |
| LangGraph | pure-Python `Orchestrator` |
| Redis queue | in-memory `asyncio` queue |
| WeasyPrint (English PDF) | pure-Python `fpdf2` Arabic RTL PDF |

### 2.2 Design invariants (never violate — this is "production-grade + responsible")

1. **Passive by default; active by explicit exception.** Active runs **only** when the RoE has
   `active_authorized = true` **and** the target is in `in_scope_domains`.
2. **No external call bypasses the Tool Abstraction Layer.** Classification check + rate-limit +
   cache + audit are enforced centrally, so no agent can skip them.
3. **No job runs without a valid, signed RoE.** The Authorization Engine is a hard gate — it
   returns an `AuthContext` or it **raises**. There is no "warn and continue".
4. **Scraping is compliant by construction** — robots.txt honored before every request, a
   transparent User-Agent, conservative pacing, exponential backoff on 429/503, public data only,
   provenance on everything. Controls in the code, not policies on paper.
5. **Deterministic risk score; the LLM explains, never invents.** Bounded ±1 band, logged, shown.
6. **Full chain of custody** — every finding traceable to source + timestamp; every active action
   logged (target, port, time, authorization).
7. **Human-authoritative** — an analyst validates before FINAL. The system **stops at
   recommendation**; it never exploits.

### 2.3 Orchestration (the active gate as a conditional stage)

The pure-Python `Orchestrator` (mirrored by the LangGraph definition) builds an ordered, checkpointed
stage list per job. The active-recon stage is **only added** when `roe.has_active_sources()` and the
subject is a domain/org — and every active tool re-checks authorization before it sends a packet:

```
authorize → osint → {geo_event | web_infra} → [active_recon: GATED] → threat_intel → analysis
          → [human validation] → report
```

### 2.4 Tool Abstraction Layer — enforces the passive/active classification

```python
class IntelTool(ABC):
    name: str
    classification: Classification        # PASSIVE | ACTIVE  (active is gated here)
    source_category: SourceCategory
    cache_ttl: int

    async def __call__(self, subject, ctx):
        ctx.assert_allows(self.classification, self.source_category, subject)  # HARD GATE — raises
        ...  # cache (passive) → rate-limit → run() → audit (chain of custody)
```

`assert_allows` refuses an ACTIVE call unless the RoE authorizes active ops *and* the subject is in
scope — proven by `tests/test_active_authorization.py` (7 scenarios, all green).

---

## PART 3 — The Agents (Collection Plane)

### 3.1 OSINT Collection Agent — PASSIVE
WHOIS/RDAP, DNS (all record types), certificate transparency (crt.sh), passive subdomain discovery,
email-pattern inference. → base entity picture.

### 3.2 Web / Infrastructure Fingerprint Agent — PASSIVE
One polite page fetch → tech stack, CDN/WAF, TLS posture; wires `IP -[EXPOSES]-> Service -[RUNS]->
Technology` so the signature CVE query walks it.

### 3.3 Geo-Event Context Agent — PASSIVE  *(the existing strength)*
Queries the GTD/GDELT-derived corpus (the 159,826-pair dataset) → geopolitical/threat-event context
for a region/timeframe. Prime RAG material for the HORUS brain.

### 3.4 Threat-Intelligence Enrichment Agent — PASSIVE
VirusTotal / OTX / AbuseIPDB (reputation), NVD/OSV (known-CVE correlation), MITRE ATT&CK mapping.

### 3.5 Network Reconnaissance Agent — **ACTIVE (GATED)**  *(the offensive capability, implemented)*
Runs only on owned/authorized targets, tools executed in order (each persists so the next sees it):
- **Active DNS / subdomain enumeration** — wordlist brute-force + resolution (`tools/active_dns_tool.py`).
- **TCP connect port scan + service/banner fingerprint** — asyncio connect scan across common ports
  on resolved IPs, light banner grab (`tools/port_scan_tool.py`).
- **Compliant web crawler/scraper** — robots-gated BFS crawl within a page/depth budget, extracting
  endpoints, forms, emails, technologies (`tools/web_crawl_tool.py`, see Part 4).
- **Absolute stop line:** discovery/enumeration only. **No exploitation, no auth attempts, no brute
  forcing credentials, no payloads.** If a feature would cross into exploitation, it is not built.

---

## PART 4 — The Precision Web-Scraping Engine (compliant by construction)

The crawler is **precise** (targeted, budgeted, same-host) and **compliant by construction** — each
rule is a code-level control, not a guideline:

1. **robots.txt first.** Fetched and parsed on entry; `can_fetch(User-Agent, url)` is checked before
   **every** request. Disallowed → skipped + logged (`robots_skip`). Disallowed paths are *recorded*
   as intelligence (they exist) but never fetched.
2. **Transparent identity.** A stable, honest `User-Agent` naming the project + a contact URL. No
   pretending to be a browser to evade detection.
3. **Conservative pacing + backoff.** Bounded page/depth budget; exponential backoff with `Retry-After`
   on HTTP 429/503 — never behaves like a DoS.
4. **Public data only.** No login/paywall/access-control circumvention; no collection behind auth.
5. **Provenance & audit.** Every fetch produces an `Evidence` record (source + timestamp + summary),
   so every scraped datum is defensible and traceable.

> **Viva-ready line:** *"Our scraper is compliant by construction: robots.txt is checked in the fetch
> layer before every request, we identify ourselves transparently, we rate-limit and back off on
> errors, we only touch public data, and we keep provenance on everything — controls in the code no
> agent can bypass."*

---

## PART 5 — The Reasoning Brain (pluggable, self-hosted or online, bilingual)

### 5.1 Role
The fine-tuned `Horus-OSINT` model becomes the **Analysis Agent**, reasoning over a **correlated
graph + RAG context** rather than a single prompt. Ground truth stays in the graph; the model
synthesizes and explains, referencing evidence — it never invents entities or scores.

### 5.2 Pluggable transport (`horus_brain/`)
`BRAIN_BACKEND` selects the transport, with a hybrid fallback chain:
- `hybrid` (default) — try **Hugging Face online**, then **local Ollama**, then grounded offline synthesis.
- `hf_serverless` — HF Inference router; `hf_endpoint` — a dedicated HF Inference Endpoint URL.
- `ollama` — self-hosted only (**data sovereignty — nothing leaves the box**; the intelligence-grade choice).

The HF transport wraps the prompt in the Llama-3 chat template and reads the model's response; every
transport degrades to a grounded, still-Arabic offline synthesis so a job always returns a report.

### 5.3 First-run setup (no hard-coded secrets)
On first launch the Command Center shows a setup modal (or `python -m core.setup_wizard`): the analyst
enters their Hugging Face token → it is validated against the HF `whoami` API → saved to `.env`. The
platform still runs (offline synthesis / local Ollama) without a token.

### 5.4 Deterministic risk scoring
```
RiskScore(entity) = 0.30·Exposure + 0.30·ThreatContext + 0.20·ReputationIntel + 0.20·Criticality
```
Deterministic base score + band; the model may adjust **±1 band max**, must log the reason, shown in
the report. Reproducible: same graph → same colors.

### 5.5 Offensive vs defensive framing
When active recon produced live attack surface (open ports / endpoints), the analysis switches to an
**offensive frame**: it surfaces ports/endpoints as prioritized findings, maps them to offensive
ATT&CK techniques (T1046, T1190, T1133, T1595), and the prompt asks the model to describe what an
adversary could do next — with defensive recommendations, and **no actual exploitation**.

### 5.6 Human-validation checkpoint
Before FINAL, an analyst sees draft findings + evidence → **Validate / Flag / Edit**. A report is only
`COMPLETED` after a `validate` action; validating renders the full deliverable set (HTML + JSON + PDF).

---

## PART 6 — Knowledge Model (Attack-Surface / Intelligence Graph)

**Nodes:** `Organization, Domain, Subdomain, IP, Port, Service, Technology, Endpoint, Certificate,
Email, Person, CVE, CloudAsset, Region, ThreatActor, Event, Indicator`.

**Edges (examples):**
```
(Organization)-[:OWNS]->(Domain)-[:HAS_SUBDOMAIN]->(Subdomain)-[:RESOLVES_TO]->(IP)
(IP)-[:HAS_OPEN_PORT]->(Port) ; (IP)-[:EXPOSES]->(Service)-[:RUNS]->(Technology)-[:HAS_VULNERABILITY]->(CVE)
(Domain)-[:HAS_ENDPOINT]->(Endpoint) ; (Email)-[:MENTIONED_ON]->(Domain)
(Region)-[:HAS_EVENT]->(Event)<-[:ASSOCIATED_WITH]-(ThreatActor)
```
Analysis becomes traversal, not manual cross-referencing; the Analysis Agent retrieves subgraphs as
grounded context; the risk-colored graph is the **single most screenshot-worthy artifact**.

```cypher
// active-recon result: owned services exposing a critical known vuln
MATCH (i:IP)-[:EXPOSES]->(s:Service)-[:RUNS]->(t:Technology)-[:HAS_VULNERABILITY]->(c:CVE)
WHERE c.cvss >= 9.0 RETURN i.address, s.name, t.name, c.id, c.cvss ORDER BY c.cvss DESC
```

---

## PART 7 — Output System (the precise, bilingual intelligence report)

### 7.1 Report structure (9 sections)
1. Executive Summary — model-authored: the picture + top findings + headline metrics.
2. Target, Scope & Authorization — the RoE, what was authorized (passive/active), sources enabled.
3. Reconnaissance / Discovered Entities — passive + (if run) active results, each with source/timestamp.
4. Context & Exposure — geo-event context and/or the mapped web/infra + attack surface.
5. Threat-Intelligence Enrichment — reputation, known-CVE references, ATT&CK mapping.
6. Attack-Surface / Intelligence Graph — rendered map, risk-colored (interactive in HTML).
7. Risk Analysis — matrix + per-finding score with component breakdown.
8. Prioritized Findings & Recommendations — evidence → why it matters → ATT&CK → recommendation.
9. Appendix — Chain of Custody — full evidence list (incl. robots decisions), the RoE, the
   active-action log, and the analyst validation record.

### 7.2 Formats & language
- **PDF** — a **real Arabic RTL PDF** built with pure-Python `fpdf2` + `arabic-reshaper` +
  `python-bidi` + a bundled Amiri OFL font (works on any OS, no system libraries). English uses
  WeasyPrint when available. Download: `GET /jobs/{id}/download/pdf`.
- **HTML** — interactive, with the live Cytoscape graph; Arabic (RTL) or English template.
- **JSON** — machine-readable full context.
- **Language** — `REPORT_LANGUAGE = ar | en`, toggled from the UI (**EN / ع**) or
  `POST /setup/language`. Switches UI, model narrative, and report together.

---

## PART 8 — Technology Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 (3.13 works) |
| API | FastAPI + Uvicorn |
| Orchestration | pure-Python `Orchestrator` (+ LangGraph-compatible definition) |
| Brain | Provider-abstracted: self-hosted Ollama **or** online Hugging Face (hybrid) |
| Active recon | asyncio TCP connect scan, dnspython enum, stdlib+httpx compliant crawler |
| Web scraping | httpx + `urllib.robotparser` + stdlib `html.parser` (+ backoff) |
| OSINT | WHOIS/RDAP, dnspython, crt.sh, Shodan/Censys (optional) |
| Threat intel | VirusTotal, OTX, AbuseIPDB, NVD/OSV, MITRE ATT&CK |
| Relational | PostgreSQL / SQLite fallback |
| Graph | Neo4j / networkx fallback |
| Vector/RAG | ChromaDB / keyword fallback |
| Cache/queue | Redis / in-memory fallback |
| Reporting | Jinja2 → HTML; fpdf2 (Arabic PDF) / WeasyPrint (English PDF); Cytoscape.js |
| Frontend | Self-contained bilingual SPA (served at `/ui`) + Cytoscape |
| Deploy | Docker + docker-compose |
| Quality | ruff (lint+format), mypy, pytest, bandit/pip-audit; GitHub Actions CI |

---

## PART 9 — Repository Structure (actual)

```
<repo-root>/
├── HORUS_Sentinel_Master_Plan.md     # THIS FILE — the constitution (source of truth)
├── README.md · LICENSE
└── horus-sentinel/                    # THE PROJECT (run everything from here)
    ├── api/           # FastAPI: jobs, demo, setup (token + language), download
    ├── core/          # authorization (passive/active gate), audit, rate_limit, jobs, db,
    │                  #   config, setup_wizard
    ├── agents/        # osint · web_infra · geo_event · threat_intel · active_recon(GATED) ·
    │                  #   analysis · report
    ├── tools/         # IntelTool ABC + whois/dns/crtsh/rdap/fingerprint/reputation/osv +
    │                  #   active_dns · port_scan · web_crawl (active)
    ├── graph/         # Attack-Surface / Intelligence Graph (networkx + Neo4j mirror)
    ├── scoring/       # deterministic risk-scoring engine
    ├── rag/           # ATT&CK (defensive + offensive) + geo corpus, retrieval
    ├── horus_brain/   # brain dispatcher · ollama provider · HF provider · prompting (AR/EN)
    ├── workflows/     # orchestrator (+ sentinel_graph LangGraph) + worker/queue
    ├── reporting/     # Jinja2 templates (AR/EN) · arabic_pdf (fpdf2) · fonts/ (Amiri)
    ├── schemas/       # RoE (active fields) · Subject · AuthContext · findings · state
    ├── horus-ui/      # bilingual Command Center (index.html)
    ├── data/          # attack_knowledge.json · geo_corpus.sample.json · reports/
    ├── deploy/        # docker-compose, Dockerfile
    ├── tests/         # ~97 tests (incl. active-recon auth gate + tools)
    └── horus-geointel/ # FROZEN placeholder for the award-winning original — do not touch
```

> **Team rule:** `horus-geointel/` is **frozen**. Build around it, never inside it.

---

## PART 10 — Build Plan (Waterfall) & Status

Rotate **Driver / Navigator / Verifier** per task. Each phase ends demoable, with a git tag.

| Phase | Scope | Status |
|---|---|---|
| 0 — Consolidation & setup | monorepo, frozen winning project, docker-compose, README | ✅ done |
| 1 — Control plane | RoE/AuthContext/Subject; Authorization Engine + **passive/active gate**; Tool ABC; `POST /jobs` | ✅ done |
| 2 — Passive collection + compliant scraping | OSINT · web-infra · geo-event · threat-intel; robots-compliant crawler | ✅ done |
| 3 — Active reconnaissance (GATED) | active DNS · port scan + fingerprint · web crawl; refuse out-of-scope (403) | ✅ done |
| 4 — Graph + risk scoring | attack-surface graph (Port/Endpoint) + deterministic scoring | ✅ done |
| 5 — Brain + reporting | pluggable HF/Ollama brain · RAG · analysis · bounded ±1 · human-validation · bilingual PDF/HTML/JSON | ✅ done |
| 6 — Orchestration end-to-end | checkpointed stages + queue/worker; job resumes after kill | ✅ done |
| 7 — Unified UI | bilingual Command Center · mode selector · active toggle · graph · Guided Demo | ✅ done |
| 8 — Hardening, deploy, pitch | CI green (ruff/mypy/pytest) · security & compliance review · deploy · demo video + slides + viva | 🔜 remaining |

**Tags:** `v0.1-foundation` … `v0.8-ui` → `v1.0-competition`.

---

## PART 11 — Why This Wins (Feature → Judging Advantage)

| Judge cares about | Feature | Why competitors lack it |
|---|---|---|
| Real, working, *capable* software | Active recon + precision scraping + fine-tuned brain, all live | Most bring passive demos or slides |
| Technical depth | Multi-agent + graph + RAG + self-hosted model + compliant scraper | Rare to have all in one |
| **Discipline / RoE (military!)** | Authorization engine gating active ops; every action logged | Most offensive demos ignore authorization |
| Legal/ethical maturity | Compliance-by-construction scraper (robots/rate/law) | Most scrapers are "smash and grab" |
| Data sovereignty | Self-hosted model — nothing leaves the infrastructure | Most call a cloud API |
| Localization | Full Arabic (RTL) report + UI + model narrative | Almost none localize |
| Hands-on trust | Judges run the Guided Demo themselves | A live demo beats any slide |
| A story they remember | "ARGUS's hundred eyes feed the Eye of HORUS" | Most have no narrative |
| Visual impact | Risk-colored attack-surface graph + real Arabic PDF | Screenshot-worthy artifacts |
| Academic anchor | Operationalizes MITRE ATT&CK TA0043 for authorized recon | Shows framework fluency |

---

## PART 12 — Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Active recon perceived as an "attack tool" | Medium | **High** | Part 0 framing; active only on owned/authorized targets; hard stop before exploitation; lead the demo with the authorization gate |
| Scraping compliance challenged in viva | Medium | Medium | Compliance-by-construction (Part 4); show the `robots_skip` log live |
| Sending intelligence queries to a US cloud | Medium | High | `BRAIN_BACKEND=ollama` — fully sovereign, nothing leaves the box |
| Breaking the winning project | Low | High | `horus-geointel/` frozen |
| Free-tier rate limits stall a phase | Medium | Medium | Cache hard; fixtures in tests |
| Nmap/WeasyPrint/Neo4j friction | Low | Low | Pure-Python fallbacks already in place (asyncio scan, fpdf2 PDF, networkx) |
| Slow CPU inference in the demo | Medium | Low | RTX Ada 5000 on the work box; offline synthesis fallback keeps the demo moving |

---

## PART 13 — Hard Viva Questions (rehearse)

**Q: "Isn't this an attack tool?"**
A: "No. It performs the *reconnaissance* phase and stops exactly where exploitation begins — no auth
attempts, no payloads, no exploitation code exists in it. Active scanning runs only on targets we own
or are authorized for, enforced by the authorization engine, and every active action is logged."

**Q: "What stops someone pointing the scanner at a target they don't own?"**
A: "The engine itself. Active tools call the authorization check *before* executing; it refuses unless
the RoE explicitly authorizes active scanning *and* lists the target in scope. A test proves the refusal
(403). In the demo we only scan our own system under an RoE we generated."

**Q: "Is your web scraping legal?"**
A: "It's compliant by construction — robots.txt checked before every request, transparent identity,
adaptive rate-limiting and backoff, public data only, provenance on everything. Controls in the code."

**Q: "Your model was trained on 2020 geopolitical data — how does it do cyber recon?"**
A: "It doesn't scan or exploit — it *reasons and reports*. Agents gather current recon and build a
graph; the model's trained skill is turning correlated intelligence into a structured, prioritized
report, grounded by RAG over the current graph and ATT&CK — and a human validates every report."

**Q: "Where does the data go?"**
A: "Nowhere it shouldn't. The model is self-hosted via Ollama by default — full data sovereignty. An
online Hugging Face mode exists for convenience, but for an intelligence deployment we run it in-house."

---

## PART 14 — Implementation Status (verified reality)

- **~97 tests pass** (`pytest -q`), including 7 active-recon authorization-gate tests and active-tool
  tests (real localhost port-scan listener, robots-compliant crawl, stubbed DNS). `ruff check` +
  `ruff format` clean.
- **The authorization gate is proven over HTTP:** out-of-scope active → 403; missing
  `active_authorized` → 403; region target → 403; in-scope + authorized → 201.
- **Real Arabic RTL PDF** renders end-to-end and downloads from the UI / API.
- **Bilingual** UI + report + model narrative; language toggle persists.
- **Pluggable brain** verified: local Ollama serves `horus-osint`; HF token validated + saved at
  first run; graceful offline synthesis when neither is reachable.
- Runs **zero-infra** (`uvicorn api.main:app`) or **full stack** (`docker compose … up`).

---

## PART 15 — Immediate Next Steps
1. Lock the Part 0 framing + the pitch until all three can say them cold. **This is the shield in the viva.**
2. On the RTX box: load the fine-tuned model into Ollama (see `horus-sentinel/RUN.md`) so the narrative
   is model-authored (`generated_by: mahmoudalyosify/Horus-OSINT` or `horus-osint`).
3. Phase 8: CI green on push, a short security/compliance review checklist, deploy, and the 3-minute
   demo video (lead with the authorization gate refusing an out-of-scope active scan).

---

*HORUS Sentinel is an authorized offensive-reconnaissance and intelligence platform for real
educational use. It performs active reconnaissance on owned/authorized targets and precision,
compliant scraping of public sources, correlates findings into an attack-surface/intelligence graph,
and uses the award-winning fine-tuned model — self-hosted for data sovereignty — as its reasoning core
to produce precise, chain-of-custody intelligence reports in Arabic or English. It executes the full
reconnaissance phase of a professional engagement — TA0043 — and stops, by design, exactly where
exploitation would begin. This document is the single technical and strategic source of truth.*
