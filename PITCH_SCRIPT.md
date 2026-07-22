<div align="center">

# 🦅 HORUS SENTINEL — ITC-Egypt 2026
## Deck Review · Enhancement Tips · Full Committee Script

*Track 3 — Intelligent Software Systems · Air Defense College · Project ID ITC-2026-T3-0726*
**Slogan:** *"The eye that judges what the eyes have seen."*

</div>

---

> **How to use this document.** Part 1 reviews the current 13-slide deck and gives prioritized,
> concrete fixes. Part 2 is a full, timed, word-for-word script you can deliver (or read from a
> teleprompter). Part 3 is Q&A preparation. Part 4 gives Arabic anchor lines for the committee.
> Everything marked **[VERIFIED]** was confirmed against the running system on 2026-07-18 — use
> those numbers with total confidence; they are your strongest asset.

---

# PART 1 — Deck review & enhancement tips

## 1.1 Verdict

The narrative spine is excellent and correctly tuned to a **military/defense committee**:
**Concept → Ethical Boundary → Architecture → Authorization (centerpiece) → Capabilities → Sovereign Brain → Trust → Localization → Academic anchor → Why we win.**
You lead with discipline and authorization, not with "hacking." That is exactly the right instinct
for this audience. The deck is already competition-grade. The tips below take it from *strong* to
*unbeatable*.

## 1.2 What's already working (keep it)

- **Ethics-first framing** (Slide 4 "IS / IS NOT", Slide 6 Authorization Engine). This wins the *Discipline / RoE* criterion before you even demo.
- **Data sovereignty** (Slide 9, self-hosted model). Resonates deeply with a defense committee.
- **Bilingual Arabic RTL deliverable** (Slide 11). Directly hits *Localization*.
- **MITRE ATT&CK anchor** (Slide 12). Gives academic legitimacy.
- **The thesis line** — *"stops exactly where exploitation would begin."* Memorable. Say it twice (open and close).
- **The myth** — ARGUS's hundred eyes *gather*; the Eye of HORUS *judges*. Culturally resonant and technically accurate (collection plane vs. reasoning plane). Use it as your cold open.

## 1.3 Top enhancement tips (in priority order)

**① Add ONE "PROOF" slide — this is your highest-impact change.**
The deck *describes* capability but doesn't *show measured reality*. Judges reward demonstrated
fact over description. Insert a proof slide (suggested position: after Slide 6, or fold into
Slide 13) with these **[VERIFIED]** numbers:

> - **104 automated tests — all green.**
> - **Live run on `example.com`** (passive, real network): **10 entities, 4 IPs, 6 findings**, all MITRE-mapped, risk-colored graph (10 nodes / 13 edges), report authored by the fine-tuned model, **Arabic PDF generated** — end to end.
> - **Out-of-scope active request → HTTP 403, refused** with a human-readable reason.
> - **Human validation required** before any report is marked FINAL.

**② Lead the demo with the REFUSAL, not the result.**
The single most persuasive 15 seconds you have: submit an out-of-scope job on stage and let the
system **say no (403)**. A recon tool that visibly *refuses* is the whole thesis made physical. Show
the "no" first; *then* show the authorized run succeeding. Discipline before capability.

**③ Reconcile the wording: "passive by default, active by authorization."**
The deck headline says *"Offensive-Reconnaissance."* For this committee that's a deliberate, strong
choice — but make the spoken narrative explicit that active recon is **double-gated** (`active_authorized = true` **and** target in `in_scope_domains`) and that everything runs **passive by default**. Never let a judge leave thinking it's an attack tool. Slide 4 + Slide 6 already carry this; reinforce it verbally every time you say "active."

**④ Fix the duplicate title (Slides 1 & 2).**
They are currently identical. If the second is an animation build, fine. If not, convert Slide 2
into a **problem/hook** slide: *"A professional reconnaissance engagement takes an analyst days.
HORUS does it in minutes — and stops at the line no machine should cross."* A committee decides in
the first 30 seconds; don't spend them twice on the same title.

**⑤ Cut on-slide text by ~40% on the dense slides (5, 6, 8, 9, 11).**
Slides should be **headline + 3–5 nouns**; the *presenter* speaks the sentences. Dense slides make
the committee read instead of listen. The script in Part 2 already carries the full detail, so the
slides can shed it safely.

**⑥ Clean up Slide 3.** Remove the two stray empty quote-mark text boxes (`"`  `"`). Keep the
English concept line and the Arabic line — that bilingual pairing is a strength.

**⑦ Add a one-line closing vision** after "Why we win": *"Ready today for authorized red-team
training and Arabic-language CTI augmentation in sovereign defense environments."* End on
deployment-readiness, not just features.

## 1.4 Per-slide quick fixes

| Slide | Current | Quick fix |
|---|---|---|
| 1 | Title | Ensure a visual gap between the wordmark **HORUS SENTINEL** and the tagline (they read merged). |
| 2 | Duplicate of 1 | Convert to **Problem/Hook** (see tip ④). |
| 3 | Core concept + 2 empty quote boxes | Delete empty boxes; keep EN + AR lines. |
| 4 | IS / IS NOT table | Strong — keep. Maybe bold *"stops at the boundary of exploitation."* |
| 5 | Four planes (dense) | Trim to plane name + 4-word descriptor; you narrate the rest. |
| 6 | Authorization engine | **Anchor your live 403 demo here.** Show the four outcomes as a truth table. |
| 7 | Active recon | Keep 3 icons; add "owned/authorized only" as a red banner. |
| 8 | Compliant scraping | Trim to the 5 control names; keep the "controls in the code" quote. |
| 9 | The Brain | Keep "Llama-3-8B / QLoRA / self-hosted"; move detail to script. |
| 10 | Trust / scoring | Keep "±1 band max" and "human validates" — these are gold. |
| 11 | Localization + 9-section report | **Anchor your Arabic-PDF demo here.** |
| 12 | MITRE ATT&CK | Keep; verbally stress *T1190 is mapped for impact but never executed.* |
| 13 | Why we win | Add the closing vision line (tip ⑦). |

## 1.5 Design & delivery polish

- **One idea per slide, one number per slide.** If a slide has a metric, make it big.
- **Contrast for the room:** dark background + high-contrast text reads from the back of a hall; risk colors (Critical red → Low green) should be legible on a projector.
- **Fonts:** ensure the Arabic (Amiri) renders in the deck, not just the PDF — a mixed-script slide that renders cleanly is itself a localization proof point.
- **Video fallback:** you have `.mp4` demos embedded — **also keep a local screen-recording and a rendered Arabic PDF on disk**. If the live demo or network fails on stage, you switch to the recording without breaking stride. Never let the network decide whether you pass.
- **Rehearse the transitions, not just the slides.** The seams between slides are where nervous presenters stall.

---

# PART 2 — Full committee script

**Total runtime:** ~12–14 minutes speaking + demo. A compressed 8-minute path is marked with ⏩.
**Format:** `[TIMING]`, then what you *say* (deliverable verbatim), then `[DO]` stage directions.
Speak in short sentences. Pause after every bold line.

> **Pre-flight checklist (do this before you walk up):**
> 1. Server running: `uvicorn api.main:app --port 8000` → open `http://localhost:8000/ui`.
> 2. Ollama up and **model pre-warmed** (send one throwaway English chat so the first real
>    answer is instant — a cold model can hit the 120 s Arabic timeout). **[VERIFIED behavior]**
> 3. Two browser tabs ready: the **UI** and the **Swagger docs** (`/docs`) for the 403 demo.
> 4. A **pre-rendered Arabic PDF** and a **screen recording** on the desktop as fallbacks.
> 5. Language toggle set to the committee's preference; know where the EN/ع button is.

---

### SLIDE 1 — Title / Cold open · [0:00–0:45]

> "Honorable committee — thank you.
> In Egyptian myth, **ARGUS had a hundred eyes that never slept.** They *gathered*. But it was the
> **Eye of HORUS** that *judged* what those eyes had seen.
> Our project is built on exactly that division of labor. A swarm of tireless eyes that collect —
> and a single, disciplined intelligence that judges.
> This is **HORUS Sentinel**: an autonomous, **authorized** reconnaissance and intelligence
> platform. And its defining feature is not what it does — it's **where it stops.**"

`[DO]` Stand still. Let "where it stops" hang for a beat before you advance.

---

### SLIDE 2 — The problem / hook · [0:45–1:30]

> "Here is the problem we solve.
> A professional reconnaissance engagement — mapping an organization's real attack surface —
> takes a skilled analyst **days** of manual work across a dozen tools. It is slow, inconsistent,
> and hard to audit.
> And the tools that automate it are usually built to *attack*. They don't know where the legal
> and ethical line is — so they cross it.
> HORUS Sentinel does the **entire reconnaissance phase of a professional engagement in minutes** —
> and it is **engineered to stop exactly at the boundary of exploitation.** Discipline is not a
> policy we wrote in a document. It is **code that cannot be bypassed.**"

`[DO]` If Slide 2 is still a duplicate title, deliver this over Slide 1 and advance faster. ⏩ In the 8-min version, merge Slides 1–2 into 45 seconds.

---

### SLIDE 3 — The core concept · [1:30–2:30]

> "So what is it, precisely?
> HORUS Sentinel is an **autonomous reconnaissance analyst.** Under a **signed authorization**, its
> agents perform **active reconnaissance on in-scope targets** and precision-scrape public
> intelligence. Everything they find is correlated into a **live attack-surface graph.** Then our
> **fine-tuned language model reasons over that graph** to produce a precise, **evidence-backed
> intelligence report.**
> It runs the full reconnaissance phase of a real engagement — and it stops the instant
> exploitation would begin."

`[DO]` For the Egyptian committee, deliver the Arabic line on the slide here (Part 4, Line A). Bilingual delivery at this exact moment is a quiet localization proof.

---

### SLIDE 4 — The boundary: Rules of Engagement · [2:30–3:45]

> "Before any architecture, let me be absolutely clear about the boundary — because for a military
> audience, this is the whole point.
> **What HORUS Sentinel IS:** authorized active recon of targets you **own or are permitted to
> test**. Discovery, enumeration, mapping, correlation, reporting. Precision scraping of **public**
> data that respects robots.txt, rate limits, and the law. It is a **red-team recon and CTI analyst
> trainer.**
> **What it is NOT:** it does **not** attack systems you don't own. It does **not** exploit — no
> payloads, no breaking in. It does **not** go behind logins or paywalls. **It is not a weapon.**
> HORUS Sentinel stops at the boundary of exploitation — **by design.** That single sentence is the
> soul of this project."

`[DO]` Point at the "IS" column, then the "IS NOT" column. Physical gesture = the committee remembers the split.

---

### SLIDE 5 — The four planes of operation · [3:45–5:00]

> "Architecturally, the system is four planes.
> **The Control Plane** is the Scope & Authorization Engine. It enforces the Rules of Engagement
> and acts as the **active gate before any operation.**
> **The Collection Plane** — ARGUS's eyes. **Passive** sources by default: OSINT, web-infra,
> geo-event, threat-intel. And **active, gated** sources: port scan, DNS enumeration, a compliant
> crawler.
> **The Knowledge Plane** builds the interconnected **attack-surface graph** and manages the
> evidence store for retrieval.
> **The Reasoning Plane** is the HORUS Brain: risk scoring, then **human validation**, then a
> **bilingual intelligence report.**
> And one engineering decision matters to this committee: **every heavy dependency — Neo4j,
> ChromaDB, Postgres, even the model host — is an *optional accelerator* with a pure-Python
> fallback.** The platform **runs with zero infrastructure.** No database, no Docker, no keys
> required. That is deployability in a sovereign environment."

`[DO]` ⏩ 8-min version: name the four planes in one breath, then jump to the sovereignty line.

---

### SLIDE 6 — The centerpiece: Authorization Engine · [5:00–6:45] · ★ LIVE DEMO

> "This is the centerpiece. **No job runs without a signed RoE.**
> And **active** reconnaissance is gated hardest. An active operation runs **only** when two
> independent conditions are both true: `active_authorized` is explicitly set — a **second,
> separate sign-off** — **and** the target is strictly inside `in_scope_domains`.
> This isn't checked politely in one agent and trusted elsewhere. It's **enforced centrally, in the
> tool abstraction layer. No agent can bypass the gate.**
> Let me show you — not tell you."

`[DO]` **★ Refusal-first demo.** Switch to the browser. Submit an out-of-scope job.

> "I'm submitting a job whose target is **not** in the authorized scope.
> Watch the response."

`[DO]` The system returns **HTTP 403** with the message:
*"web_infra is enabled but 'notmine.example' is not in in_scope_domains … passive infra collection is confined to owned assets."* **[VERIFIED]**

> "**403 — refused.** The machine said *no*, and it told me *why*, in plain language, and it logged
> it. **This is discipline you can audit.** Out-of-scope, refused. Missing the authorization flag,
> refused. A region or asset you don't own, refused. Only in-scope **and** authorized returns 201
> and runs."

`[DO]` Now submit the **authorized** `example.com` job and let it start. Move to Slide 7 while it runs.

---

### SLIDE 7 — Active reconnaissance (gated capability) · [6:45–7:35]

> "When — and only when — a target is owned and authorized, three active capabilities come online,
> designed strictly for **discovery and enumeration**, never exploitation.
> A **TCP-connect port scan** with service and banner fingerprinting, to map the live attack
> surface. **Active DNS enumeration** — subdomain discovery by wordlist and resolution. And a
> **compliant web crawler** that maps endpoints, forms, exposed emails, and technologies —
> responsibly.
> Every one of these runs **only** behind the gate you just watched refuse an unauthorized
> request."

---

### SLIDE 8 — Precision scraping: compliant by construction · [7:35–8:25]

> "Our scraper is **compliant by construction** — the rules are **code-level controls, not
> guidelines on paper.**
> It checks **robots.txt first**, before every request; disallowed paths are logged and skipped.
> It carries a **transparent, honest User-Agent** that identifies the project — **no browser
> spoofing.** It uses **conservative pacing** with exponential backoff on 429 and 503 — it can
> **never behave like a denial-of-service attack.** It touches **public data only** — no login, no
> paywall circumvention. And **every fetch is stored with its source and timestamp** for full
> provenance.
> As we say in the code review: **those aren't policies bolted on top — they're controls no agent
> can bypass.**"

---

### SLIDE 9 — The Brain: self-hosted, sovereign, fine-tuned · [8:25–9:35]

> "The reasoning is powered by our own fine-tuned model — **Horus-OSINT**, built on **Llama-3-8B
> with QLoRA.**
> The transport is **pluggable**: run it **self-hosted via Ollama**, or online via Hugging Face.
> And the **default is self-hosted** — for an intelligence deployment, **nothing leaves your
> infrastructure. Data sovereignty is the default, not an option.**
> Critically, the model is **RAG-grounded.** It reasons over the **current attack-surface graph and
> MITRE ATT&CK — not its training memory.** It **references evidence** and it does **not invent
> entities or scores.**
> And there are **no hard-coded secrets** — the analyst enters their token securely on first run.
> If no model is reachable at all, the system **gracefully degrades to offline synthesis**, so a
> report is **always** produced."

`[DO]` **[VERIFIED]** you may add: "Live, our self-hosted model just authored a full report and answered analyst questions directly — I'll show the output in a moment."

---

### SLIDE 10 — Trust: deterministic scoring & human-in-the-loop · [9:35–10:35]

> "For a defense committee, an AI you can't trust is an AI you can't use. So we bounded it.
> The risk score is **deterministic**: the **same graph produces the same score and the same
> colors, every time.** Reproducible.
> The AI is **bounded**: the model may adjust that score by **at most one risk band**, and it
> **must log the reason.** It advises; it cannot overrule the math.
> Every claim in the report has a **chain of custody** — traceable to a specific **source tool and
> timestamp.**
> And above all: the system is **AI-augmented but human-authoritative.** A **human analyst must
> validate** the findings before any report is marked **FINAL.** The machine drafts. **The officer
> decides.**"

`[DO]` "The machine drafts, the officer decides" — say it slowly. It's your trust thesis in six words.

---

### SLIDE 11 — Localized deliverable: Arabic & English · [10:35–11:50] · ★ DEMO

> "And the deliverable is built for **this** audience — natively.
> **One toggle** switches the entire experience — the UI direction from left-to-right to
> right-to-left, the **model's narrative language**, and the **report language** — instantly.
> The Arabic report is a **real right-to-left PDF**, built in **pure Python** with fpdf2 and the
> Amiri font — **no system libraries, works on any operating system.**
> And it ships in **three formats**: interactive **HTML** with a live graph, **JSON** for
> downstream tooling, and **PDF.** The report itself is **nine sections** — from executive summary
> through the attack-surface graph and risk analysis to a **chain-of-custody appendix.**"

`[DO]` **★** Open the authorized `example.com` result from the earlier run. Show the **risk-colored graph**, then **download the Arabic PDF** and open it. **[VERIFIED]** — the live run produced **10 entities, 4 IPs, 6 findings**, MITRE-mapped, with a valid Arabic PDF.

> "This is the run I authorized four minutes ago — ten correlated entities, six prioritized
> findings, every one mapped to MITRE ATT&CK, and here is the **intelligence report, in Arabic**,
> generated by our sovereign model."

---

### SLIDE 12 — Academic anchor: MITRE ATT&CK TA0043 · [11:50–12:40]

> "Academically, we are **operationalizing the first tactic of MITRE ATT&CK — Reconnaissance,
> TA0043.**
> Our active scanning maps to **T1595** and **T1046.** Our information gathering maps to **T1590,
> T1592, T1589.** External discovery to **T1133 and T1596.**
> And this is important: **T1190 — Exploit Public-Facing Application — is mapped in our reports to
> show the defender the *potential impact* of an exposure. But it is never, ever performed.**
> We show defenders **exactly what an adversary would discover — so they can see their own exposure
> first, and close it.**"

---

### SLIDE 13 — Why HORUS Sentinel wins · [12:40–13:40] · Close

> "So let me close against your own criteria.
> **Real, capable software?** Active recon, compliant scraping, and a fine-tuned brain — all live,
> and backed by **104 automated tests, all green.**
> **Military discipline and Rules of Engagement?** An authorization engine that gates every active
> operation — you watched it refuse one — and logs every action.
> **Legal and ethical maturity?** A scraper that's compliant by construction.
> **Data sovereignty?** A self-hosted model — nothing leaves the infrastructure.
> **Localization?** A full Arabic right-to-left report, UI, and model narrative.
> **Visual impact?** A risk-colored interactive graph and a native Arabic PDF.
> HORUS Sentinel is **ready today** for authorized red-team training and Arabic-language cyber
> threat-intelligence in a sovereign defense environment.
> ARGUS's hundred eyes gather. **The Eye of HORUS judges.** And it knows exactly where to stop.
> Thank you — we welcome your questions."

`[DO]` Stop talking. Don't fill the silence. Let the close land.

---

# PART 3 — Q&A preparation

Answer in **one sentence first**, then one supporting sentence. Never ramble.

| Likely question | Crisp answer |
|---|---|
| **"Isn't this just a hacking tool?"** | "No — it performs only reconnaissance, and it's engineered to refuse anything outside a signed authorization; you saw it return 403. It stops before exploitation, in code that no agent can bypass." |
| **"What's actually novel — recon tools exist."** | "Three things together: a centrally-enforced authorization gate, a *fine-tuned, RAG-grounded* reasoning model that cites evidence instead of hallucinating, and a native Arabic deliverable — as one integrated, auditable pipeline." |
| **"How do you prevent misuse by the operator?"** | "Active recon is double-gated — an explicit `active_authorized` sign-off *and* the target inside `in_scope_domains` — every action is logged with a chain of custody, and a human must validate before anything is final." |
| **"Does the AI hallucinate findings or scores?"** | "It can't drive the score — scoring is deterministic and reproducible; the model may nudge it by at most one band and must log why, and it's RAG-grounded to the graph and MITRE, so it references evidence and never invents entities." |
| **"What if there's no GPU / no internet / no database?"** | "It runs with zero infrastructure — pure-Python fallbacks for the graph, retrieval, and PDF, and offline synthesis if no model is reachable; heavy services are optional accelerators." |
| **"How do we trust the Arabic output quality?"** | "The Arabic PDF is real RTL, shaped with the Amiri font, and the narrative comes from the model in Arabic; English is faster, and we pre-warm the model so Arabic generation stays within budget." |
| **"Is it tested? How do we know it works?"** | "104 automated tests pass, and we verified it live end-to-end: a real passive run on example.com produced 10 entities, 6 MITRE-mapped findings, a risk graph, and an Arabic PDF — while an out-of-scope request was refused with 403." |
| **"Can it scale to a real engagement?"** | "Yes — there's an async worker and a queue backend; jobs can be enqueued and processed out-of-band, and the datastores swap to Postgres/Neo4j/Chroma for a production deployment." |
| **"What data does it send outside?"** | "By default, nothing — the model is self-hosted; the only outbound traffic is the passive OSINT lookups you authorize (DNS, RDAP, certificate transparency), each logged." |

**If the live demo fails on stage:** "Networks are the one thing we don't control — here's the
recorded run and the rendered Arabic report," and switch to your local fallbacks. Composure *is* the
discipline you're claiming.

---

# PART 4 — Arabic anchor lines (optional, for the committee)

Deliver these at the marked moments for a bilingual touch. Keep them short and confident.

- **Line A — Slide 3 (core concept):**
  «محلل استطلاع هجومي ذاتي: تحت تفويضٍ موقّع، يُجري استطلاعًا فعّالًا على أهدافٍ مصرّحٍ بها، ويقف عند حدّ الاستغلال — بالتصميم.»

- **Line B — Slide 10 (trust):**
  «الآلة تُعِدّ المسودة، والضابط يقرّر. لا يصبح أي تقرير نهائيًا إلا بعد تحقّق محلل بشري.»

- **Line C — Close (Slide 13):**
  «عيونُ أرجوس المئة تجمع، وعينُ حورس تحكم — وتعرف تمامًا أين تتوقف.»

---

<div align="center">

**HORUS SENTINEL** · *The eye that judges what the eyes have seen.*
Built for **authorized, disciplined, sovereign** defense. Passive by default · active by authorization · human-validated.

</div>
