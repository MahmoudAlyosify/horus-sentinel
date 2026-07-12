---
marp: true
theme: default
paginate: true
size: 16:9
header: 'HORUS SENTINEL · ITC-Egypt 2026 · Track 3'
footer: 'Authorized offensive reconnaissance · passive · auditable · human-validated'
style: |
  section { font-size: 26px; }
  h1 { color: #0d2844; }
  h2 { color: #1d4e79; }
  table { font-size: 20px; }
  code { color: #b5179e; }
  .small { font-size: 20px; color: #555; }
  .win { color: #2e8b57; font-weight: 700; }
  .stop { color: #d7263d; font-weight: 700; }
---

<!--
HOW TO TURN THIS INTO A .PPTX / .PDF
------------------------------------
This is a Marp markdown deck. Install Marp CLI (npm i -g @marp-team/marp-cli), then:
    marp HORUS_Sentinel_Pitch_Deck.md --pptx      # -> HORUS_Sentinel_Pitch_Deck.pptx
    marp HORUS_Sentinel_Pitch_Deck.md --pdf       # -> PDF
Or use the "Marp for VS Code" extension: open this file → Export slide deck → PPTX.
Slides are separated by `---`. Speaker notes are in HTML comments under each slide.
Edit freely — this is a starting scaffold mapped to the judging criteria.
-->

# 🦅 HORUS SENTINEL

## Autonomous, Authorized Offensive-Reconnaissance & Intelligence Platform

**ITC-Egypt 2026 · Track 3 — Intelligent Software Systems · Air Defence College**

<span class="small">Project ID: ITC-2026-T3-0726 · Supervisor: Sarah Mohammed Taha Khater · Team: Mahmoud · Mirna · Sondos</span>

> *"ARGUS's hundred eyes gather the intelligence — the Eye of HORUS delivers the judgment."*

<!-- Speaker notes: Open with the myth. Two names, one honest system: ARGUS = the collection swarm, HORUS = the reasoning brain. 15 seconds, then move. -->

---

## The one-sentence pitch (memorize it)

> **"HORUS Sentinel is an autonomous offensive-reconnaissance analyst. Under a signed
> authorization, its agents perform active reconnaissance on in-scope targets and
> precision-scrape public intelligence, correlate everything into a live attack-surface
> graph, and our fine-tuned model — self-hosted for full data sovereignty — reasons over it
> to produce a precise, evidence-backed intelligence report. It runs the full reconnaissance
> phase of a professional engagement, and stops exactly where exploitation would begin."**

<span class="small">🇪🇬 «محلل استطلاع هجومي ذاتي: تحت تفويض موقّع، يجري استطلاعًا فعّالًا على أهداف مصرّح بها، يربطها في رسم سطح هجوم حيّ، ويحكم عليها نموذجنا المُحسَّن — مستضاف ذاتيًا بسيادة كاملة على البيانات — ليخرج تقريرًا استخباراتيًا دقيقًا. يقف عند حدّ الاستغلال بالتصميم.»</span>

<!-- Speaker notes: Say it in one breath. This is the whole project in 4 lines. All three team members must be able to say it cold. -->

---

## The problem

The **reconnaissance phase** of any security or intelligence task is:

- 🐌 **Slow** — hours to days, a dozen CLI tools and browser tabs
- 🧩 **Fragmented** — findings live in separate tabs; correlation is done by hand
- 🎯 **Inconsistent** — coverage depends on what the analyst remembers to check
- 🔁 **Not reproducible** — no audit trail of *what was checked, when, from where*
- 🎓 **Untrainable** — no safe, auditable environment to *learn* professional recon end-to-end

**HORUS Sentinel automates that phase and produces a professional deliverable from it.**

<!-- Speaker notes: This is a documented real problem: analyst data-overload in the recon phase. Frame it as both an ops problem and a training problem (fits a college). -->

---

## The boundary — what makes this responsible, not disqualified

| ✅ What HORUS Sentinel IS | <span class="stop">❌ What it is NOT</span> |
|---|---|
| **Authorized** active recon of targets you **own / have permission for** | Attacking systems you don't own |
| **Discovery & enumeration** — mapping, correlation, reporting | **Exploitation** — payloads, breaking in |
| **Precision scraping** of **public** data (robots + rate + law) | Smash-and-grab, behind logins/paywalls |
| A **red-team recon** & **CTI analyst** trainer | A weapon |

**It stops at the boundary of exploitation — by design.**

<!-- Speaker notes: A military audience respects rules of engagement more than raw capability. This slide is your shield. Lead with discipline. -->

---

## Architecture — four planes

```
CONTROL      → Scope & Authorization Engine (RoE · scope · ACTIVE gate) + Orchestrator
COLLECTION   → ARGUS "eyes":  PASSIVE (OSINT · web-infra · geo-event · threat-intel)
                              ACTIVE-GATED (port scan · active DNS · compliant crawler)
KNOWLEDGE    → Postgres/SQLite · Neo4j/networkx graph · ChromaDB/keyword RAG · evidence
REASONING    → HORUS Brain (self-hosted OR online fine-tuned Llama-3) → risk scoring →
               human validation → bilingual Intelligence Report (PDF / HTML / JSON)
```

**Every heavy dependency is an optional accelerator with a pure-Python fallback** → runs
zero-infra with `uvicorn`, or full-stack with `docker compose`.

<!-- Speaker notes: Emphasize graceful degradation — it always runs. Judges can run it on any laptop with nothing pre-installed. -->

---

## ⭐ The centerpiece — the Authorization Engine

**No job runs without a valid, signed RoE. Active recon is gated hardest.**

An active operation runs **only** when the RoE has:
- `active_authorized = true` (an explicit second sign-off), **AND**
- the target is inside `in_scope_domains`

```text
Out-of-scope active request      → 403  (refused before any packet)
Missing active_authorized flag   → 403
Region / non-owned subject       → 403
In-scope + authorized            → 201  → runs
```

<span class="small">Enforced centrally in the Tool Abstraction Layer + proven by `tests/test_active_authorization.py` (7 scenarios).</span>

<!-- Speaker notes: DEMO THIS FIRST. "Watch it refuse an active scan against a target we're not authorized for." That refusal is the feature. This wins the responsibility criterion outright. -->

---

## Active reconnaissance (gated capability)

Runs **only** on owned/authorized targets — discovery/enumeration only:

- 🔌 **TCP connect port scan + service/banner fingerprint** — live attack surface
- 🌐 **Active DNS / subdomain enumeration** — wordlist brute-force + resolution
- 🕷️ **Compliant web crawler/scraper** — endpoints, forms, emails, technologies

<span class="stop">Absolute stop line:</span> **no exploitation · no auth attempts · no credential brute-force · no payloads.** Every active action is logged (target, port, time, authorization).

<!-- Speaker notes: If a feature would cross into exploitation, it is not built. Say that explicitly. The discovery/defensive alternative is documented instead. -->

---

## Precision scraping — compliant *by construction*

Each rule is a **code-level control**, not a guideline:

1. **robots.txt first** — `can_fetch()` checked before **every** request; disallowed → skipped + logged
2. **Transparent identity** — honest User-Agent + contact URL (no browser spoofing)
3. **Conservative pacing + exponential backoff** on 429/503 — never DoS-like
4. **Public data only** — no login/paywall circumvention
5. **Provenance & audit** — every fetch stored with source + timestamp

> *"Those aren't policies bolted on top — they're controls in the code no agent can bypass."*

<!-- Speaker notes: Rehearse this answer for the "is scraping legal?" question. Show the robots-skip log live if asked. -->

---

## The brain — self-hosted, sovereign, fine-tuned

- 🧠 Our **award-winning fine-tuned `Horus-OSINT`** (Llama-3-8B, QLoRA) as the reasoning core
- 🔀 **Pluggable transport:** self-hosted via **Ollama** *or* online via **Hugging Face** (hybrid)
- 🔒 **Data sovereignty:** default is self-hosted — **nothing leaves the infrastructure**
- 🔑 **First-run setup:** the analyst enters their HF token, validated + saved — no hard-coded secrets
- 📚 **RAG-grounded:** reasons over the graph + MITRE ATT&CK, not its training memory
- 🧾 The model **explains**; it never invents entities or scores

<!-- Speaker notes: Data sovereignty is a killer line for a military judge. "Most competitors call a cloud API; our model runs in-house." -->

---

## The Intelligence Knowledge Graph

- Findings become a **queryable, risk-colored attack-surface graph** (not scattered tabs)
- Analysis becomes **traversal**, not manual cross-referencing
- The single **most screenshot-worthy artifact** — put it on every slide

```cypher
MATCH (i:IP)-[:EXPOSES]->(s:Service)-[:RUNS]->(t:Technology)-[:HAS_VULNERABILITY]->(c:CVE)
WHERE c.cvss >= 9.0
RETURN i.address, s.name, t.name, c.id, c.cvss ORDER BY c.cvss DESC
```

<span class="small">🔴 red = look here first. Nodes: Domain · Subdomain · IP · Port · Service · Technology · Endpoint · CVE · …</span>

<!-- Speaker notes: SHOW the live Cytoscape graph here. Pan, zoom, click a red node. This is the visual wow moment. -->

---

## Trust — deterministic scoring + human-in-the-loop

```
RiskScore = 0.30·Exposure + 0.30·ThreatContext + 0.20·Reputation + 0.20·Criticality
```

- **Deterministic & reproducible** — same graph → same score & colors
- The model may adjust **±1 band max**, must **log the reason**, shown in the report
- Every claim is **traceable to a source + timestamp** (chain of custody)
- A **human analyst validates** before any report is FINAL

> **AI-augmented, human-authoritative.**

<!-- Speaker notes: This answers "why should we trust the AI?" head-on. Don't apologize for the human step — it's a designed control and a selling point. -->

---

## Academic anchor — MITRE ATT&CK TA0043

The platform operationalizes the **first tactic** of ATT&CK — Reconnaissance:

- **T1595** Active Scanning · **T1046** Network Service Discovery
- **T1590 / T1592 / T1589** Gather victim network / host / identity info
- **T1133** External Remote Services · **T1596** Search open technical databases
- Downstream risk only: **T1190** Exploit Public-Facing App *(mapped, never performed)*

**We show defenders exactly what an adversary would discover — so they see their exposure first.**

<!-- Speaker notes: This is the academic thesis, defensible in any viva. Framework fluency scores with judges. -->

---

## Localized deliverable — Arabic (RTL) & English

- 🌍 **Bilingual** — UI, model narrative, and report switch **Arabic ⟷ English** (one toggle)
- 📄 **Real Arabic RTL PDF** — pure-Python (fpdf2 + Amiri font), works on any OS, no system libs
- 🖥️ **HTML** with the live interactive graph · **JSON** for downstream tooling
- 🧾 9-section report: exec summary → scope/RoE → findings → graph → risk → recommendations → chain of custody

<span class="small">Serves an Arabic-speaking intelligence audience natively — almost no competitor localizes.</span>

<!-- Speaker notes: Open the generated Arabic PDF live. It reads right-to-left, properly shaped, professional. Tangible, memorable. -->

---

## Why this wins — feature → judging criterion

| Judge cares about | Our feature |
|---|---|
| Real, capable software | Active recon + compliant scraping + fine-tuned brain, all **live** |
| Technical depth | Multi-agent + graph + RAG + self-hosted model |
| <span class="win">Discipline / RoE (military!)</span> | Authorization engine gating active ops; every action logged |
| Legal/ethical maturity | Compliance-by-construction scraper |
| Data sovereignty | Self-hosted model — nothing leaves the box |
| Localization | Full Arabic report + UI + narrative |
| Hands-on trust | Judges run the **Guided Demo** themselves |
| Visual impact | Risk-colored attack-surface graph + real Arabic PDF |

<!-- Speaker notes: This is the scorecard slide. Tie each feature to a criterion explicitly. -->

---

## Live demo script (≈3 minutes)

1. **Lead with the gate** → submit an active scan on an *unauthorized* target → **403**. *"By design."*
2. **Guided Demo** → one click → agents run → **risk-colored graph** appears
3. **Open a red node** → its risk, evidence, ATT&CK mapping
4. **Analyst validates** → report flips to FINAL
5. **Download the Arabic PDF** → the professional deliverable
6. *(optional)* switch language **ع → EN**; show `generated_by: horus-osint` (self-hosted)

<span class="small">Runs on the RTX Ada 5000 box; degrades gracefully to offline synthesis anywhere.</span>

<!-- Speaker notes: Hand the judge the laptop. A live demo beats any slide. Practice the timing until it's under 3 minutes with no dead air. -->

---

## Verified status & viva-ready answers

**Status:** ~97 tests pass · lint/format clean · 403 gate proven over HTTP · real Arabic PDF renders · bilingual · self-hosted brain live.

**Q: "Isn't this an attack tool?"** → *"No — recon phase only, stops before exploitation; active runs only on authorized targets, enforced by the engine, every action logged."*
**Q: "What stops an out-of-scope scan?"** → *"The engine refuses before any packet — there's a test that proves it (403)."*
**Q: "Is the scraping legal?"** → *"Compliant by construction — robots, transparent identity, backoff, public data only, provenance."*
**Q: "Where does the data go?"** → *"Nowhere — the model is self-hosted. Full data sovereignty."*

<!-- Speaker notes: All three members must be fluent on: authorization, scraping compliance, active scope, model/sovereignty, scoring, ethics. Rehearse under time. -->

---

# Thank you 🦅

## HORUS SENTINEL — *the Eye that judges what the eyes have seen*

**Passive by default · active by explicit authorization · auditable · human-validated · sovereign · bilingual**

<span class="small">github.com/MahmoudAlyosify/horus-sentinel · 🤗 mahmoudalyosify/Horus-OSINT · ITC-2026-T3-0726</span>

<!-- Speaker notes: Close on the discipline line. Restate: we run the full reconnaissance phase, responsibly, and stop where exploitation begins. Invite them to run the demo themselves. -->
