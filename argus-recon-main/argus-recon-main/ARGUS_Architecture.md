# ARGUS — AI-Driven Autonomous Reconnaissance System

**Autonomous Reconnaissance & Ground-truth Understanding System**

*A multi-agent External Attack Surface Management (EASM) platform for authorized red-team and threat-intelligence operations.*

> **Technical Design Whitepaper — v1.0**
> Audience: engineering, security architecture, hiring reviewers
> Status: design specification for a 2-month build

---

## 0. Positioning & Scope Statement (read this first)

ARGUS automates the **reconnaissance phase** of an *authorized* security assessment. It is, in product terms, an **External Attack Surface Management (EASM) platform** with an LLM reasoning layer on top. That positioning matters for three reasons:

1. **It is an established, fundable product category.** Shodan Monitor, Censys ASM, Microsoft Defender EASM, and the open-source SpiderFoot all occupy this space. Framing the project this way signals domain literacy, not just scripting ability.
2. **It defines a hard ethical/legal boundary.** ARGUS discovers and analyzes a target's *publicly exposed* attack surface and prioritizes risk. It **stops at recommendation**. It does not exploit, brute-force, deliver payloads, or establish access. Reconnaissance maps to MITRE ATT&CK tactic **TA0043 (Reconnaissance)** and **TA0042 (Resource Development)** — discovery and analysis, not intrusion.
3. **Authorization is a first-class architectural component, not a checkbox.** Every active operation is gated behind a Scope & Authorization Engine. Passive OSINT (which only consumes already-public data) is permitted broadly; active scanning (which touches target infrastructure) requires an explicit, signed Rules-of-Engagement (RoE) record. This is exactly how professional tooling is built, and it is one of the strongest "production-grade" signals you can put on a CV.

**Design invariant:** *No active probe leaves the system without a matching authorization record. Passive-by-default; active-by-exception.*

---

## 1. High-Level System Overview

### 1.1 The problem

The reconnaissance phase of any engagement is the most time-consuming and least standardized. A human operator manually pivots across dozens of tools and data sources — WHOIS, DNS, certificate transparency, Shodan, code repositories, breach corpora, technology fingerprints — then mentally correlates the fragments into an attack-surface picture. This is:

- **Slow** — days of manual collection per target.
- **Inconsistent** — coverage depends on operator memory and discipline.
- **Poorly correlated** — findings live in disconnected tool outputs; relationships (this subdomain → this IP → this exposed service → this known CVE) are reconstructed by hand.
- **Hard to prioritize** — raw findings vastly outnumber the few that actually matter.

### 1.2 What ARGUS does

ARGUS ingests a single authorized target (`target.com` + an RoE record), then orchestrates a team of specialized AI agents to:

1. **Collect** passive OSINT and (when authorized) active network/web signals.
2. **Correlate** every finding into a unified **Attack Surface Graph** (assets and the relationships between them).
3. **Enrich** assets with threat-intelligence reputation data.
4. **Reason** over the graph with an LLM to identify exposure, prioritize risk, and map findings to known adversary techniques.
5. **Report** a structured, evidence-backed intelligence deliverable (Executive Summary → Technical Findings → Attack Surface Map → Risk Analysis → Remediation).

### 1.3 Real-world use cases

| Use case | How ARGUS is used | Output consumed by |
|---|---|---|
| **Red teaming** | Accelerate the recon phase; produce a prioritized surface map before engagement planning | Red team lead |
| **Penetration testing** | Standardize and document recon; produce the recon section of the pentest report automatically | Pentest engineer / client |
| **Continuous EASM (blue team)** | Run on your *own* org on a schedule; alert on newly exposed assets ("shadow IT") | SOC / security engineering |
| **Threat intelligence** | Profile infrastructure and exposure of a known-malicious or third-party entity | CTI analyst |
| **M&A / vendor risk** | Assess the external posture of an acquisition target or supplier | GRC / due diligence |

The blue-team / EASM angle is worth emphasizing in any writeup: the *same engine* that maps an adversary's view of a target is the engine a defender uses to find their own exposure first.

---

## 2. System Architecture

### 2.1 Logical architecture

```
                              ┌──────────────────────────┐
                              │        User / API         │
                              │  target + RoE submission  │
                              └─────────────┬─────────────┘
                                            │
                              ┌─────────────▼─────────────┐
                              │  Scope & Authorization     │  ◄── HARD GATE
                              │  Engine (RoE validation,   │      passive vs active
                              │  allowlist, rate budget)   │      classification
                              └─────────────┬─────────────┘
                                            │ authorized job
                              ┌─────────────▼─────────────┐
                              │   Recon Orchestrator       │
                              │   (LangGraph state machine)│
                              └─────────────┬─────────────┘
              ┌────────────────┬────────────┼────────────┬────────────────┐
              ▼                ▼             ▼            ▼                ▼
       ┌──────────┐    ┌──────────────┐ ┌─────────┐ ┌──────────┐  ┌──────────────┐
       │  OSINT   │    │   Network    │ │   Web    │ │  Threat  │  │   Analysis   │
       │  Agent   │    │ Recon Agent  │ │ Finger-  │ │  Intel   │  │ & Reasoning  │
       │ (passive)│    │   (active*)  │ │ printing │ │  Agent   │  │ Agent (LLM)  │
       └────┬─────┘    └──────┬───────┘ └────┬─────┘ └────┬─────┘  └──────┬───────┘
            │                 │              │            │               │
            └─────────────────┴──────┬───────┴────────────┘               │
                                      ▼                                    │
                          ┌───────────────────────┐                       │
                          │  Tool Abstraction Layer│  (rate-limited,       │
                          │  + Collection workers   │   cached, auditable) │
                          └───────────┬─────────────┘                      │
                                      ▼                                     │
                  ┌───────────────────────────────────────┐               │
                  │            Knowledge Base               │◄──────────────┘
                  │  Postgres (relational)  +  Neo4j        │   reads graph,
                  │  (Attack Surface Graph) + Chroma (RAG)  │   writes reasoning
                  │  + Redis (cache/queue) + Object store    │
                  └───────────────────┬─────────────────────┘
                                      ▼
                          ┌───────────────────────┐
                          │    Reporting Agent     │  Jinja2 → HTML → WeasyPrint → PDF
                          └───────────┬─────────────┘
                                      ▼
                          PDF / HTML / JSON deliverable
```

`*` Active = the operation touches target infrastructure (e.g., port scan). Permitted only with a matching RoE record.

### 2.2 The four architectural layers

1. **Control plane** — Scope & Authorization Engine + Orchestrator. Decides *what is allowed* and *what runs next*.
2. **Collection plane** — the five collection/enrichment agents + the Tool Abstraction Layer. Decides *how to gather a signal* and normalizes every external tool behind one rate-limited, cached, audited interface.
3. **Knowledge plane** — relational store, graph store, vector store, cache, object store. The single source of truth; agents never pass large blobs to each other, they write to the KB and pass references.
4. **Reasoning & delivery plane** — Analysis Agent + Reporting Agent. Turns the graph into prioritized intelligence and a deliverable.

### 2.3 Orchestration model (LangGraph)

ARGUS uses **LangGraph** rather than a linear pipeline because reconnaissance is a *fan-out / converge* problem with conditional re-entry:

- New subdomains discovered by OSINT must **feed back** into Network and Web agents (a subdomain found in week-1 collection becomes a scan target).
- The graph is a **stateful state machine**: nodes are agents, edges are transitions, and a shared `ReconState` object carries job metadata, the authorization context, and references to KB records.
- Conditional edges implement the authorization gate: the Network Agent node is only reachable when `state.roe.active_scanning_authorized == True`.
- Checkpointing makes long jobs resumable and auditable (every state transition is persisted).

```python
# workflows/recon_graph.py  (skeleton — orchestration, not attack code)
from langgraph.graph import StateGraph, END
from schemas import ReconState

def build_recon_graph():
    g = StateGraph(ReconState)

    g.add_node("authorize",   authorization_gate)     # validates RoE, classifies scope
    g.add_node("osint",       osint_agent)            # always allowed (passive)
    g.add_node("network",     network_agent)          # active — gated
    g.add_node("web",         web_fingerprint_agent)  # mostly passive
    g.add_node("threat_intel",threat_intel_agent)     # passive enrichment
    g.add_node("analysis",    analysis_agent)         # LLM reasoning
    g.add_node("report",      reporting_agent)

    g.set_entry_point("authorize")
    g.add_edge("authorize", "osint")

    # fan-out after OSINT seeds the surface
    g.add_edge("osint", "web")
    g.add_conditional_edges(
        "osint",
        lambda s: "network" if s.roe.active_scanning_authorized else "threat_intel",
        {"network": "network", "threat_intel": "threat_intel"},
    )
    g.add_edge("network", "threat_intel")
    g.add_edge("web", "threat_intel")

    # converge → reason → report
    g.add_edge("threat_intel", "analysis")
    g.add_edge("analysis", "report")
    g.add_edge("report", END)
    return g.compile(checkpointer=postgres_checkpointer)
```

### 2.4 Tool Abstraction Layer

Every external integration (Shodan, Censys, crt.sh, WHOIS, DNS resolvers, Nmap, VirusTotal, etc.) implements one interface. This is where the **non-negotiable operational controls** live, so individual agents cannot bypass them:

```python
class ReconTool(ABC):
    name: str
    classification: Literal["passive", "active"]   # drives the authorization gate
    rate_limit: RateBudget                          # per-source token bucket
    cache_ttl: int                                  # avoid re-querying public sources

    @abstractmethod
    async def run(self, target: Target, ctx: AuthContext) -> ToolResult: ...

    async def __call__(self, target, ctx):
        ctx.assert_allows(self.classification, target)  # raises if unauthorized/out-of-scope
        if cached := await cache.get(self.cache_key(target)):
            return cached
        await self.rate_limit.acquire()
        result = await self.run(target, ctx)
        await audit_log.record(self.name, target, ctx, result.summary())  # chain of custody
        await cache.set(self.cache_key(target), result, ttl=self.cache_ttl)
        return result
```

Three properties fall out of this design: **rate-limiting and ToS compliance** are enforced centrally; **caching** prevents hammering public sources (politeness + cost control); and **every external touch is audit-logged** for chain of custody — essential for a tool used in regulated engagements.

---

## 3. AI Agent Design

All agents share a contract: they read a `Target` + `AuthContext`, call tools through the abstraction layer, write normalized findings to the Knowledge Base, and return a typed Pydantic result. Below, each agent's input, output schema, tools, and logic.

### 3.1 OSINT Collection Agent  *(classification: passive)*

**Mission:** Build the initial picture of the organization from already-public data. This agent is always permitted because it never touches target infrastructure — it queries third-party data brokers and public records.

- **Tools:** WHOIS/RDAP, DNS resolution (A/AAAA/MX/TXT/NS/CNAME), certificate transparency (crt.sh, Censys certs), passive DNS, subdomain enumeration via public sources (no brute force), public code-repo search (GitHub/GitLab metadata & secret-pattern hits in public repos), breach-corpus lookups via reputable APIs (e.g., HaveIBeenPwned), search-engine dorking.
- **Logic:** Seed with the apex domain → expand domains/subdomains via CT logs and passive DNS → resolve each to IPs → extract org metadata, MX providers, and email patterns → flag exposed artifacts (public repo secrets, leaked credentials in breach corpora) as candidate findings. Subdomain discovery here is *passive* (public sources); active DNS brute-forcing, if ever used, is reclassified as active and gated.

```json
{
  "company_name": "Example Corp",
  "domains": ["example.com", "example.net"],
  "subdomains": [
    {"host": "vpn.example.com", "source": "crt.sh", "resolved_ips": ["203.0.113.10"]}
  ],
  "email_pattern": "{first}.{last}@example.com",
  "emails": ["jane.doe@example.com"],
  "employees": [{"name": "Jane Doe", "role": "DevOps", "source": "public_profile"}],
  "exposed_artifacts": [
    {"type": "public_repo_secret_pattern", "repo": "example/infra", "confidence": 0.6}
  ]
}
```

### 3.2 Network Reconnaissance Agent  *(classification: active — gated)*

**Mission:** Characterize exposed infrastructure. **This is the one agent that touches target systems**, so it is the most tightly controlled: it only runs when `roe.active_scanning_authorized` is true, only against in-scope IP ranges in the RoE, and within the configured rate budget.

- **Tools:** Shodan API and Censys API (these are *passive* — they read pre-collected internet-wide scan data, no packets to the target); Nmap (this is *active* — direct probing, gated).
- **Logic:** First exhaust passive sources (Shodan/Censys) to learn open ports/services without touching the target. Only if RoE authorizes active scanning, run a bounded Nmap service/version scan against in-scope hosts to confirm and fill gaps. Collect open ports, service banners, product/version strings, and TLS metadata (cert chain, expiry, weak protocol/cipher support). No exploitation, no auth attempts, no payloads — discovery only.

```json
{
  "host": "203.0.113.10",
  "discovery_method": "shodan",
  "ports": [
    {"port": 443, "service": "https", "product": "nginx", "version": "1.25.3",
     "banner": "...", "tls": {"protocols": ["TLSv1.2","TLSv1.3"], "cert_expiry": "2026-01-04"}},
    {"port": 8080, "service": "http-proxy", "product": "Jenkins", "version": "2.426"}
  ],
  "in_scope": true
}
```

### 3.3 Web Fingerprinting Agent  *(classification: mostly passive)*

**Mission:** Identify the technology stack of discovered web assets.

- **Tools:** Wappalyzer-style fingerprint engine, BuiltWith API, a custom HTTP(S) client that fetches headers + a single page (lightweight, polite, rate-limited), favicon hashing, and known-path probing **only if** active scanning is authorized.
- **Logic:** For each web-facing host, fetch response headers and landing markup → match against a fingerprint database → identify CMS, web framework, JS libraries, CDN/WAF, analytics, and cloud provider (via IP ranges + headers + CNAME chains, e.g., AWS/GCP/Azure/Cloudflare). Record version evidence where exposed (powers later CVE correlation).

```json
{
  "host": "www.example.com",
  "framework": "Next.js",
  "cms": null,
  "js_libraries": [{"name": "React", "version": "18.2"}],
  "cdn": "Cloudflare",
  "waf_detected": true,
  "cloud_provider": "AWS",
  "server_headers": {"server": "cloudflare", "x-powered-by": null}
}
```

### 3.4 Threat Intelligence Enrichment Agent  *(classification: passive)*

**Mission:** Attach reputation and threat context to discovered assets.

- **Tools:** VirusTotal, AlienVault OTX, AbuseIPDB, Shodan tags, public CVE feeds (NVD / OSV) for version → known-vulnerability mapping.
- **Logic:** For each IP/domain/service, query reputation sources → aggregate into a normalized reputation score and a list of indicators (malicious associations, blocklist hits, historical abuse). For each `product+version` discovered by the Network/Web agents, look up *known, published* CVEs (informational correlation — ARGUS reports that a version has known CVEs; it does not weaponize them).

```json
{
  "asset": "203.0.113.10",
  "reputation": "neutral",
  "reputation_score": 0.12,
  "malicious_indicators": [],
  "blocklist_hits": 0,
  "known_cves": [
    {"product": "Jenkins 2.426", "cve": "CVE-2024-XXXXX", "cvss": 9.8, "source": "NVD"}
  ]
}
```

### 3.5 Analysis & Reasoning Agent  *(LLM — the "brain")*

**Mission:** Turn correlated findings into prioritized, explained intelligence. This is where the LLM earns its place — not for collection, but for **synthesis, prioritization, and explanation** that would otherwise require a senior operator.

- **Models:** Pluggable provider layer — Claude / GPT-4o-class / Llama 3 (self-hosted for sensitive engagements). The choice is abstracted behind one interface so the engine isn't vendor-locked.
- **Technique:** **RAG over the Attack Surface Graph + a MITRE ATT&CK knowledge base.** The agent retrieves relevant subgraphs and ATT&CK technique descriptions (TA0043 reconnaissance techniques, plus common initial-access *risk indicators*) and reasons over them. Grounding the LLM in retrieved facts + the graph dramatically reduces hallucination versus free-form prompting.
- **Responsibilities:** Correlate findings across agents; identify exposure clusters; map findings to ATT&CK techniques; assess and explain risk; recommend **remediation** (defensive framing); produce the natural-language Executive Summary.

**Important design choice on "attack paths":** ARGUS frames these as **exposure narratives with remediation**, exactly like a professional pentest report does. Example output:

> *Finding:* Jenkins 2.426 is exposed on `203.0.113.10:8080` with no WAF and a known critical CVE.
> *Why it matters:* Exposed CI/CD consoles are a recurring initial-access and supply-chain risk (ATT&CK T1190 – Exploit Public-Facing Application is a known risk pattern for this exposure class).
> *Risk:* **Critical.**
> *Recommendation:* Remove public exposure; place behind VPN/SSO; patch to a fixed release; enable WAF.

The agent describes *that* an exposure is risky and *why*, and tells the defender how to close it. It does not generate exploit code or step-by-step intrusion instructions — that boundary is what keeps the tool a recon/EASM platform rather than an attack tool.

```json
{
  "executive_summary": "Example Corp exposes ... The most significant risk is ...",
  "prioritized_findings": [
    {
      "id": "F-001",
      "asset": "203.0.113.10:8080",
      "title": "Internet-exposed Jenkins with known critical CVE",
      "risk": "critical",
      "risk_score": 91,
      "attack_ck_mapping": ["T1190"],
      "evidence_refs": ["network:port-8080", "ti:CVE-2024-XXXXX"],
      "recommendation": "Restrict to VPN/SSO, patch, enable WAF"
    }
  ]
}
```

### 3.6 Report Generation Agent

**Mission:** Assemble the deliverable.

- **Tools:** Jinja2 templates → HTML → WeasyPrint → PDF; D3/Cytoscape export for the interactive graph; raw JSON export for machine consumption.
- **Logic:** Pull the finalized graph + prioritized findings + summary from the KB → render a templated report with consistent branding, a risk matrix, the attack-surface map, and an appendix of evidence with source attribution and collection timestamps (chain of custody). Output PDF + HTML + JSON.

---

## 4. Data Pipeline

### 4.1 Collection

- Agents enqueue collection tasks to a **Redis-backed work queue**; async workers execute them through the Tool Abstraction Layer.
- Every external call is **rate-limited per source** (token bucket), **cached** (TTL per source — CT logs change slowly, reputation faster), and **audit-logged**.
- Raw responses are written to an **object store** (MinIO/S3) keyed by `job_id/source/asset/timestamp` — immutable evidence.

### 4.2 Normalization & storage

Findings are normalized into canonical entities and persisted across purpose-built stores:

| Store | Technology | Holds |
|---|---|---|
| Relational | PostgreSQL | Jobs, RoE/authorization records, audit log, normalized findings, users |
| Graph | Neo4j (or `networkx` for MVP) | The **Attack Surface Graph** — assets + relationships |
| Vector | ChromaDB | Embedded findings + MITRE ATT&CK corpus for RAG retrieval |
| Cache / queue | Redis | Tool-result cache, rate budgets, task queue |
| Object store | MinIO / S3 | Immutable raw tool output (evidence) |

### 4.3 Processing & flow between agents

The core principle: **agents communicate through the Knowledge Base, not by passing large blobs.** The LangGraph `ReconState` carries only the `job_id`, the `AuthContext`, and lightweight references. This keeps state small, makes every step resumable from a checkpoint, and means the graph is the single source of truth that the Analysis Agent reasons over.

```
seed target ─► OSINT writes domains/subdomains/IPs ─► graph updated
            ─► (gated) Network reads new IPs, writes ports/services
            ─► Web reads web hosts, writes tech stack
            ─► Threat Intel reads all assets, writes reputation + CVE links
            ─► Analysis reads full graph (RAG), writes prioritized findings
            ─► Reporting reads findings + graph, emits deliverable
```

---

## 5. Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| **Language** | Python 3.12 | Ecosystem for security + AI |
| **Backend / API** | FastAPI + Uvicorn | Async, typed, auto OpenAPI docs |
| **Agent orchestration** | LangGraph (core) + LangChain (tool/LLM adapters) | Stateful, conditional, checkpointed graph — fits fan-out/converge recon |
| **LLM layer** | Provider-abstracted: Claude / GPT-4o-class / Llama 3 (self-host via Ollama/vLLM for sensitive work) | No vendor lock-in; self-host option for confidential targets |
| **Relational DB** | PostgreSQL | Jobs, auth records, audit log, findings |
| **Graph DB** | Neo4j (prod) / networkx (MVP) | Attack Surface Graph + path queries |
| **Vector DB** | ChromaDB (MVP) → Pinecone/pgvector (scale) | RAG over findings + ATT&CK |
| **Cache / queue** | Redis | Caching, rate budgets, task queue |
| **Object store** | MinIO (local) / S3 (cloud) | Immutable evidence |
| **OSINT/recon tools** | WHOIS/RDAP, dnspython, crt.sh, Shodan, Censys, Wappalyzer, BuiltWith, Nmap (gated) | Discovery & fingerprinting |
| **Threat intel** | VirusTotal, AlienVault OTX, AbuseIPDB, NVD/OSV | Enrichment & CVE correlation |
| **Reporting** | Jinja2 + WeasyPrint; Cytoscape.js/D3 for graphs | HTML→PDF + interactive map |
| **Frontend (optional)** | React + Tailwind + Cytoscape.js | Job dashboard + graph viewer |
| **Packaging / deploy** | Docker + docker-compose → AWS ECS/EC2 | Reproducible, portfolio-friendly |
| **Observability** | Structured logging, OpenTelemetry, Prometheus/Grafana | "Production-grade" signal |
| **CI/CD** | GitHub Actions (lint, type-check, test, build, scan) | Polish for the GitHub portfolio |

---

## 6. Attack Surface Modeling

### 6.1 The graph model

ARGUS represents the target as a **typed property graph**. This is the single most differentiating technical idea in the project — it turns disconnected tool output into a queryable model.

**Nodes:** `Organization`, `Domain`, `Subdomain`, `IP`, `Service`, `Technology`, `Certificate`, `Email`, `Employee`, `CVE`, `CloudAsset`.

**Edges (relationships):**

```
(Organization)-[:OWNS]->(Domain)
(Domain)-[:HAS_SUBDOMAIN]->(Subdomain)
(Subdomain)-[:RESOLVES_TO]->(IP)
(IP)-[:EXPOSES]->(Service)
(Service)-[:RUNS]->(Technology)
(Technology)-[:HAS_VULNERABILITY]->(CVE)
(Service)-[:SECURED_BY]->(Certificate)
(IP)-[:HOSTED_ON]->(CloudAsset)
(Organization)-[:HAS_EMPLOYEE]->(Employee)
```

### 6.2 Why a graph

Once findings are a graph, exposure analysis becomes **graph traversal**:

- *"Which internet-facing services run technology with a known critical CVE?"* → a single Cypher query, not manual cross-referencing.
- *"Which subdomains share an IP with a high-risk service?"* → neighborhood query.
- The Analysis Agent retrieves **subgraphs** (an asset + its 1–2 hop neighborhood) as grounded context for the LLM — far more reliable than dumping raw JSON into a prompt.

```cypher
// exposed services carrying a critical known vuln
MATCH (i:IP)-[:EXPOSES]->(s:Service)-[:RUNS]->(t:Technology)-[:HAS_VULNERABILITY]->(c:CVE)
WHERE c.cvss >= 9.0 AND i.internet_facing = true
RETURN i.address, s.port, t.name, c.id, c.cvss
ORDER BY c.cvss DESC
```

### 6.3 Exposure identification

An asset's exposure is a function of: internet-reachability, service sensitivity (admin panels, CI/CD, databases, VPN > static marketing site), authentication posture, presence of a WAF/CDN, TLS hygiene, and known-vulnerability linkage. These feed the risk score (next section).

---

## 7. Risk Scoring System

### 7.1 Design goals

A score that is **explainable** (every point is attributable to evidence), **reproducible** (same inputs → same score), and **AI-augmented but not AI-dependent** (the LLM adjusts and explains; it does not invent the number).

### 7.2 The model

Each asset's risk is a weighted composite of four sub-scores, each normalized to 0–100:

```
RiskScore(asset) = w_e · Exposure
                 + w_t · TechRisk
                 + w_i · ThreatIntel
                 + w_c · Criticality

default weights:  w_e = 0.30   w_t = 0.30   w_i = 0.20   w_c = 0.20
```

| Sub-score | Drives off | Examples |
|---|---|---|
| **Exposure** | Reachability + sensitivity of what's exposed | Open admin panel +high; behind VPN/WAF −; no auth +high |
| **TechRisk** | Known CVEs on detected versions | Maps highest associated CVSS → contribution; EOL software penalty |
| **ThreatIntel** | Reputation / abuse signals | Blocklist hits, malicious associations from VT/OTX/AbuseIPDB |
| **Criticality** | Asset class weighting | CI/CD, identity, database, VPN > generic web |

### 7.3 Where the LLM contributes

The deterministic formula produces a **base score and a category** (Critical / High / Medium / Low / Info). The Analysis Agent then:

1. **Contextualizes** — adjusts within a band when the graph reveals compounding factors (e.g., an exposed admin panel *and* leaked credentials for that domain in a breach corpus → escalate within band, with the reason logged).
2. **Explains** — generates the human-readable justification and remediation.
3. **Never silently overrides** — any LLM adjustment is bounded (e.g., ±1 band), recorded with its rationale, and visible in the report. This keeps the score auditable.

```python
def risk_score(asset, graph, ti) -> RiskResult:
    exposure  = score_exposure(asset, graph)       # 0..100
    tech      = score_tech_risk(asset, ti.cves)    # 0..100
    intel     = score_threat_intel(ti)             # 0..100
    crit      = ASSET_CRITICALITY[asset.kind]      # 0..100
    base = 0.30*exposure + 0.30*tech + 0.20*intel + 0.20*crit
    band = to_band(base)                           # Critical/High/Medium/Low/Info
    return RiskResult(base=base, band=band,
                      components={"exposure":exposure,"tech":tech,
                                  "intel":intel,"criticality":crit})
```

---

## 8. Output System

### 8.1 Report structure

1. **Executive Summary** — LLM-authored, non-technical: posture in a paragraph, top 3–5 risks, headline metrics (assets discovered, internet-facing services, critical findings).
2. **Discovered Assets** — domains, subdomains, IPs, with source + timestamp.
3. **Network Exposure** — open ports, services, banners, TLS posture.
4. **Technology Stack** — frameworks, CMS, CDN/WAF, cloud providers.
5. **Email & Employee Intelligence** — patterns and public-profile findings (with a privacy note).
6. **Attack Surface Map** — the rendered graph (interactive in HTML, static image in PDF).
7. **Risk Analysis** — risk matrix + per-finding scores with component breakdown.
8. **Prioritized Findings & Recommendations** — each finding: evidence → why it matters → ATT&CK mapping → **remediation**.
9. **Appendix** — full evidence list with source attribution and collection times (chain of custody) + the RoE record under which the assessment ran.

### 8.2 Formats

- **PDF** (Jinja2 → WeasyPrint) — the client deliverable.
- **HTML** — interactive, with the live graph viewer.
- **JSON** — machine-readable, for ingestion into other tooling (SIEM, ticketing).

---

## 9. 8-Week Execution Plan

> Each week ends with something demonstrable and committed. The order front-loads passive capability (safe, always-runnable) and gates active scanning behind the authorization engine built in week 1.

| Week | Theme | Implementation | Deliverable |
|---|---|---|---|
| **1** | **Foundation + Authorization Engine** | Repo scaffold, Docker, FastAPI skeleton, Pydantic schemas, Postgres, **Scope & Authorization Engine + RoE model**, Tool Abstraction Layer (rate-limit/cache/audit) | Running API that accepts a target+RoE; passive/active classification enforced; architecture diagram in README |
| **2** | **OSINT Agent (passive)** | WHOIS/RDAP, DNS, crt.sh, passive subdomain enum, email patterns, breach lookups; write to graph | `POST /jobs` returns discovered domains/subdomains/IPs for a real (your-own) target |
| **3** | **Network Agent + graph** | Shodan/Censys (passive) → ports/services; gated Nmap; Neo4j/networkx Attack Surface Graph with relationships | Graph populated; Cypher queries for exposed services |
| **4** | **Web Fingerprinting + Threat Intel** | Wappalyzer/BuiltWith/custom fingerprinting; VirusTotal/OTX/AbuseIPDB enrichment; NVD/OSV CVE correlation | Tech stack + reputation + known-CVE links on assets |
| **5** | **LangGraph orchestration** | ✅ COMPLETE: Agents (OSINT, Network, Web, ThreatIntel) wired into StateGraph; conditional auth gate (Network node skipped if unauthorized); API endpoint `/jobs/{id}/run-workflow` invokes full pipeline; 32 tests passing (4 new workflow tests) | Full recon workflow executable end-to-end via single HTTP POST; job status transitions correctly; passive/active split enforced by graph topology |
| **6** | **Analysis Agent (LLM + RAG)** | Provider-abstracted LLM; ChromaDB + MITRE ATT&CK corpus; RAG over subgraphs; risk-scoring engine | Prioritized, explained findings with ATT&CK mapping + scores |
| **7** | **Reporting engine** | Jinja2 templates, WeasyPrint PDF, Cytoscape graph render, JSON export, chain-of-custody appendix | Full PDF + HTML + JSON report from a single job |
| **8** | **Polish + deploy** | Tests, CI (GitHub Actions), observability, hardening, Docker Compose, deploy to AWS, demo video, docs | Public repo, live demo, recorded walkthrough, README/whitepaper |

---

## 10. Production & Portfolio-Quality Enhancements

These are what move the project from "good student project" to "this person could build our platform." Pick the ones you have time for; the first three are highest-leverage.

1. **Multi-agent orchestration with LangGraph** *(core)* — already in the design; emphasize the stateful, conditional, checkpointed graph in your writeup. This is the headline architectural skill.
2. **RAG grounded in MITRE ATT&CK** — embed the ATT&CK reconnaissance/resource-development corpus; map every finding to a technique ID. Demonstrates real CTI literacy and modern RAG engineering in one feature.
3. **The Attack Surface Graph + visualization** — an interactive Cytoscape/D3 graph is the single most screenshot-worthy artifact for LinkedIn/CV. A picture of a target's surface, color-coded by risk, sells the whole project.
4. **Continuous EASM mode** — schedule recurring runs against your *own* domain and diff results to surface *newly exposed* assets ("you stood up a new subdomain yesterday; here it is"). This reframes the project as a defensive product and broadens your audience.
5. **Explainable, auditable risk scoring** — the component breakdown + bounded LLM adjustment with logged rationale. Reviewers notice when scoring is principled rather than a magic number.
6. **Provider-abstracted, self-hostable LLM layer** — show it running on Claude/GPT *and* a self-hosted Llama 3 via Ollama. Signals you think about data sensitivity and cost, not just calling one API.
7. **Authorization & chain-of-custody as features** — a `--scope` RoE file, an immutable audit log, and a report appendix that proves what ran when. This is the maturity signal most portfolio projects in this space lack, and it directly answers the first question any security hiring manager will ask.
8. **Polish layer** — full test suite, GitHub Actions CI, Prometheus/Grafana dashboards, a clean README with the architecture diagram, and a 3-minute demo video. The demo video matters more than people expect for LinkedIn reach.

---

## Appendix A — Suggested Repository Structure

```
argus-recon/
├── api/                      # FastAPI app, routes, job submission
├── core/
│   ├── authorization.py      # Scope & Authorization Engine, RoE model
│   ├── audit.py              # chain-of-custody logging
│   └── rate_limit.py
├── agents/
│   ├── osint_agent.py
│   ├── network_agent.py
│   ├── web_agent.py
│   ├── threat_intel_agent.py
│   ├── analysis_agent.py
│   └── report_agent.py
├── tools/                    # ReconTool implementations
│   ├── base.py               # ReconTool ABC (rate-limit/cache/audit)
│   ├── whois_tool.py
│   ├── dns_tool.py
│   ├── crtsh_tool.py
│   ├── shodan_tool.py
│   ├── censys_tool.py
│   ├── nmap_tool.py          # active — gated
│   ├── fingerprint_tool.py
│   └── threatintel_tool.py
├── graph/                    # Attack Surface Graph models + queries
├── scoring/                  # risk-scoring engine
├── rag/                      # ATT&CK corpus, embeddings, retrieval
├── workflows/
│   └── recon_graph.py        # LangGraph orchestration
├── reporting/                # Jinja2 templates, PDF/HTML/JSON renderers
├── schemas/                  # Pydantic models (ReconState, findings, RoE)
├── frontend/                 # optional React + Cytoscape dashboard
├── tests/
├── deploy/                   # docker-compose, AWS, CI
└── README.md
```

## Appendix B — Responsible Use

ARGUS is built for **authorized** assessments only: your own assets, or targets you have written permission to assess. Passive OSINT consumes already-public data; active scanning touches target infrastructure and is legally meaningful — run it only under a signed Rules-of-Engagement record, which the Scope & Authorization Engine requires by design. Respect third-party API terms of service and rate limits (enforced centrally in the Tool Abstraction Layer). The system maps exposure and recommends remediation; it deliberately stops short of exploitation. Treating authorization, scope, and auditability as first-class features isn't just compliance — it's the difference between a tool a security team can actually adopt and one they can't.
