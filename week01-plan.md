# MinimalLM — LUHME 2026 Unified Execution Plan (Merged)

**Supersedes:** `week01-plan.md` (2026-07-03) and `week01-new-plan.md` (2026-07-04). This is the single source of truth from here forward for the LUHME track.

*"Say Less, Mean More: Decoding-Time Verbosity Control for Clearer Human–AI Communication"*
CISC 898 · Queen's University, School of Computing · Supervisor: Dr. Rahatara Ferdousi
GitHub: [github.com/MahmoudAlyosify/minimal-lm](https://github.com/MahmoudAlyosify/minimal-lm)

**Prepared:** July 4, 2026 · **Submission deadline: July 15, 2026 (confirmed directly by the supervisor) → 11 days remaining.**

---

## Team

| Name              | Role      | Student ID | NetID  | Email                       |
| ----------------- | --------- | ---------- | ------ | --------------------------- |
| Mahmoud Alyosify  | Team Lead | 20595453   | 25bbdf | mahmoud.alyosify@queensu.ca |
| Mirna Imbabi      | Member    | 20596311   | 25JPDD | Mirna.imbabi@queensu.ca     |
| Eman Elkhamisi    | Member    | 20596329   | 25xbvh | 25xbvh@queensu.ca           |
| Elsayed Elmandoua | Member    | 20596379   | 25XRVL | elsayed.elmandoua@queensu.ca |

---

## 0. How to Use This Document

1. Single source of truth for the **LUHME 2026 track**. The original technical Master Plan (TRR, latency, O(N²) KV-cost framing) is **Track B** — a larger paper for later — and is paused. Nothing below should be read as an efficiency claim.
2. **Write continuously in Overleaf** — the day something is read, decided, or drafted. The supervisor's explicit rule, not optional.
3. Every claim carries a citation someone on the team has personally opened and read. No second-hand citations.
4. **Epistemic convention used throughout (keep this habit):**
   - ✅ **VERIFIED** = checked against the primary source on 2026-07-03/04 (URL given).
   - ⚠️ **CONFLICT / UNCERTAIN** = sources disagree or could not be confirmed — must be resolved before we rely on it.
   - 🔎 **LEAD — VERIFY BEFORE CITING** = a plausible pointer for your literature search; do not cite until you have read the actual paper.

---

## 1. The Critical Reframing — Track A vs. Track B

We are running **two framings of one project**. Confusing them will damage both.

|                                      | **Track A — LUHME 2026 workshop paper (NOW)**                                                                                                                               | **Track B — Full conference paper (LATER, master plan)**                                |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Core question                        | Does verbose/redundant generation harm human–AI understanding and conversational alignment, and can decoding-time verbosity control improve clarity?                              | Can training-free logit reshaping reduce output tokens with minimal quality loss (efficiency)? |
| Framing                              | **Language understanding & human communication problem** (per Dr. Ferdousi's explicit instruction: *"we are not framing this as an efficiency paper"*)                     | Efficiency: TRR, latency, O(N²) KV-read argument                                              |
| Headline metrics                     | Clarity, redundancy, perceived understanding, semantic preservation, conciseness (e.g., ConCISE-style) — human-centered                                                           | TRR, ROUGE/BERTScore/EM-F1, TTFT/TPS                                                           |
| Datasets                             | Conversational / instruction data — supervisor suggests**AlpacaEval or MT-Bench**                                                                                           | SQuAD, CNN/DM, XSum                                                                            |
| What stays identical                 | The**mechanism**: training-free verbosity-aware decoding via a `LogitsProcessor` (composite penalty + entropy gate), all four invariants from the master plan (Appendix A) | Same mechanism                                                                                 |
| What must NOT appear as the headline | Token-cost/latency/economics framing (can appear as a secondary observation at most)                                                                                               | —                                                                                             |

**Practical consequences for everything you write this week:**

1. The Introduction opens with a *communication* problem (clarity, ambiguity, alignment), not a compute-cost problem.
2. Related Work is organized around verbosity-as-a-communication-failure, over-generation in dialogue, conciseness evaluation, and alignment — with efficient-inference work (LazyLLM, SlimInfer, speculative decoding) appearing only as brief positioning ("decoding-time intervention is feasible"), never as baselines.
3. The evaluation section is designed around **how humans experience the output**, with automatic metrics supporting (not replacing) that story.
4. The master plan's technical invariants still bind the method: (i) zero-weights identity, (ii) EOS-only length term, (iii) entropy as multiplicative gate, (iv) stateless-from-`input_ids`. The math does not change because the framing changed.

**LUHME topics of interest we map onto** (✅ VERIFIED from the CfP, https://luhme.up.pt/call-for-papers/): "Language understanding in LLMs", "Turn-taking, repair, and alignment in human–AI interaction", "Evaluation of LU", "Discourse, pragmatics and LU", "Effects and risks of language misunderstanding", "Manifestations of language (mis)understanding". Pick 1–2 of these to name explicitly in the paper's framing — decide as a team in the next meeting (Decision 3).

---

## 2. LUHME 2026 — Verified Submission Facts

All checked on **2026-07-03** against https://luhme.up.pt/paper-submission/ and https://luhme.up.pt/call-for-papers/.

| Item               | Requirement                                                                                                                                                                                                                                                                                                                        |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Language           | English                                                                                                                                                                                                                                                                                                                            |
| Template           | **ACL LaTeX template** (github.com/acl-org/acl-style-files)                                                                                                                                                                                                                                                                  |
| Length             | **≤ 8 pages**; references + ethics/limitations sections do **not** count toward the limit                                                                                                                                                                                                                             |
| Review             | **Double-blind** — no author names, no identifying acknowledgments, anonymized artifact links                                                                                                                                                                                                                               |
| Submission portal  | OpenReview:`EMNLP/2026/Workshop/LUHME` (https://openreview.net/group?id=EMNLP/2026/Workshop/LUHME)                                                                                                                                                                                                                               |
| Originality        | Original, unpublished; no substantial overlap with work accepted as a full paper in another archival forum.**Non-archival workshop papers and preprints are fine** — important: this keeps Track B (a later, larger conference paper) viable, but the conference version must go substantially beyond the workshop version. |
| Registration       | ≥1 author must register by the early registration deadline to present; prerequisite for proceedings inclusion                                                                                                                                                                                                                     |
| Proceedings        | Intended publication in the**ACL Anthology** (as in 2024 & 2025 editions)                                                                                                                                                                                                                                                    |
| Ethics/Limitations | "Authors are encouraged to include an ethics and/or a limitations section" — we WILL include both (also matches our project's honesty standards)                                                                                                                                                                                  |
| **Deadline** | **July 15, 2026 — confirmed directly by the supervisor.** (Two earlier candidate dates — 31 May 2026 on the official site, 30 June 2026 per a LINGUIST List CFP repost — were both already past by the time we checked on July 4; the supervisor's confirmation supersedes both. Treat July 15 as final.)                 |

### 2.1 OpenReview logistics (do not leave this to the last week)

- All four members + supervisor need **OpenReview profiles**; new profiles (especially with non-institutional emails) can take days to activate. Create them **Day 1** with `@queensu.ca` emails.
- For double-blind: the public repo `github.com/MahmoudAlyosify/minimal-lm` **cannot be linked as-is** in the submission. Use an anonymized mirror (e.g., anonymous.4open.science) or state "code released upon acceptance."

---

## 3. Previous LUHME Proceedings — What "Accepted" Looks Like Here

✅ VERIFIED proceedings volumes:

- 1st LUHME (2024): https://aclanthology.org/volumes/2024.luhme-1/
- 2nd LUHME (2025): https://aclanthology.org/volumes/2025.luhme-1/ (published Bologna, October 2025; ~10 papers + invited talk)

The 2025 volume mixes: **empirical LLM-evaluation studies** (e.g., "Do Large Language Models understand how to be judges?" — `2025.luhme-1.9`, confirmed real), **survey papers** (e.g., Anikina et al., "Building Common Ground in Dialogue: A Survey," `2025.luhme-1.2`, confirmed real), **position/conceptual papers** (e.g., terminologists as stewards of meaning), and **applied NLP studies** (native-language identification, MT preference tuning, discourse/topic-sentiment analysis, visual entailment probing).

**Takeaway:** a focused, well-executed empirical study with a human-centered evaluation fits squarely. We do not need (and should not attempt) a 5-dataset, 3-model benchmark blitz in 8 pages. Careful evaluation methodology (rubrics, human alignment, agreement statistics) is what this venue scrutinizes. Papers that connect a technical intervention to a *language-understanding claim* are the sweet spot — exactly the supervisor's reframing.

**Task (all members, Phase 1):** each member reads **2 papers from the 2025 proceedings** (pick different ones; the LLM-as-judge paper and the common-ground survey are mandatory picks for whoever takes evaluation and alignment respectively — Mirna) and writes a 5-bullet summary answering: What claim? What method? What evaluation? What would a LUHME reviewer have liked/criticized? What does this teach us about how to present *our* paper? → commit to `/reading/luhme_proceedings/` and paste key takeaways into the Overleaf "venue notes" comment block.

---

## 4. Roles & Workstreams

Dr. Ferdousi's four workstreams and her "12 additional papers (3 each)" requirement, mapped one-to-one. Everyone additionally reads the three core papers (Section 6.1).

| Member                   | Workstream (from supervisor's doc)                                                                              | 3-paper search topic                             | Primary Overleaf sections                                                   |
| ------------------------ | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------- |
| **Mahmoud** (lead) | (1) Problem framing & related work; owns Overleaf structure, submission logistics, OpenReview, ACL template     | **Verbosity in LLMs**                      | Introduction, Related Work §"Verbosity & length biases"                    |
| **Elsayed**        | (2) Repetition & lexical redundancy detection: n-gram overlap, duplicate-phrase detection as a decoding penalty | **Redundancy reduction in generated text** | Method §"Lexical redundancy signal", Related Work §"Redundancy reduction" |
| **Eman**           | (3) Semantic similarity methods: sentence embeddings, quantifying semantic overlap between generated segments   | **Over-generation in dialogue systems**    | Method §"Semantic redundancy signal", Related Work §"Over-generation"     |
| **Mirna**          | (4) Evaluation protocols: human-centered evaluation (clarity, usefulness, redundancy, perceived understanding)  | **Conversational alignment in LLMs**       | Evaluation section, Related Work §"Alignment & human evaluation"           |

**Cross-cutting rules (apply regardless of role):**

- Everyone participates in the joint reading of the three core papers and the joint methodology discussion. No siloed knowledge.
- Interpretation and conclusions are produced **in team discussion**, not by any tool. Use AI assistance to gather/verify/structure — the analysis in Overleaf must be yours.
- Every claim you write in Overleaf carries a citation you have personally opened and read. No second-hand citations.

---

## 5. Compressed Schedule (July 4–15)

The original plan assumed a full week of open-ended reading before a "next meeting" finalized four items. With 11 days total to a **submission-ready** paper, that finalization meeting moves to **Day 3 (July 6)**, not the end of the week.

### Phase 1 — Prep Sprint (Sat Jul 4 – Sun Jul 5)

| Owner   | Task                                                                                                             | Deliverable                                                                                                        |
| ------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Mahmoud | Problem framing & related work; confirm submission guidelines (Section 2)                                        | Introduction v0 + Related Work skeleton in Overleaf; 3 papers on "verbosity in LLMs"                               |
| Elsayed | Repetition/lexical redundancy methods; frame n-gram/duplicate-phrase detection as a decoding penalty             | One-page technical note; 3 papers on "redundancy reduction in generated text"                                      |
| Eman    | Semantic similarity methods; sentence embeddings vs. unembedding-row cosine for the decode loop                  | One-page comparison note + Semantic-Eval repo runnability check; 3 papers on "over-generation in dialogue systems" |
| Mirna   | Evaluation protocols; human-centered dimensions (clarity, usefulness, redundancy, perceived understanding)       | Draft evaluation-dimensions table; 3 papers on "conversational alignment in LLMs"                                  |
| All     | Joint reading: ConCISE, Semantic-Eval, Speculative Speculative Decoding (Kumar et al. 2026), Chiang & Lee (2023) | 5-bullet summary per paper in`/reading/`                                                                         |

### Phase 2 — Supervisor Meeting (Mon Jul 6)

Close, with the supervisor, the six decisions in Section 9. Full agenda: paper title (3–5 candidates) · decoding formulation in LUHME language · dataset (AlpacaEval vs. MT-Bench) · evaluation protocol (including the annotator/ethics question).

### Phase 3 — Execution (Tue Jul 7 – Sun Jul 12)

- Adapt prompts/data loader to the chosen dataset (open-ended instructions, not SQuAD-style spans).
- Run the zero-weights identity test first — all results are invalid until it passes.
- Run baseline and MinimalLM arms; collect outputs for both.
- Collect evaluations per the Decision-2 protocol (human ratings and/or length-controlled LLM-judge).
- Compute statistics: Wilcoxon signed-rank p-value, bootstrap 95% CI, rank-biserial effect size for every comparison claim.

### Phase 4 — Writing & Review (Mon Jul 13 – Tue Jul 14)

Complete all Overleaf sections; full team read-through, top to bottom. Prepare the anonymized version for double-blind review (strip author names, identifying acknowledgments, non-anonymized repo links).

### Phase 5 — Submission (Wed Jul 15)

Submit via OpenReview early in the day — not at the deadline.

---

## 6. Literature Review Protocol

### 6.1 Core Assigned Papers — Verified Citations & Reading Questions

**Paper 1 — ConCISE** ✅ VERIFIED
*"ConCISE: A Reference-Free Conciseness Evaluation Metric for LLM-Generated Answers"*, Ghafari et al. (Commonwealth Bank of Australia), arXiv:2511.16846. https://arxiv.org/abs/2511.16846

What it does: a reference-free conciseness metric computed as the average of three compression-based components — (i) compression ratio vs. an LLM *abstractive* summary of the response, (ii) compression ratio vs. an LLM *extractive* summary, (iii) *word-removal* compression (an LLM removes as many non-essential words as possible while preserving meaning; the removable fraction indicates verbosity). Evaluated on WikiEval; validated for alignment with human judgment.

**Read it to answer (write answers in your template):**

1. How exactly do they *define* conciseness vs. redundancy? Quote their operational definitions — ours must be at least as precise.
2. What is their human-evaluation setup (raters, items, scale, agreement)? The supervisor said this paper guides our evaluation design.
3. Cost profile: every ConCISE score requires multiple LLM calls. If we adopt it, what does scoring, say, 300 outputs × 2 systems cost in calls/time? Is a subset-scoring design needed?
4. Failure modes they report — where does the metric disagree with humans?
5. Gap we can state honestly: ConCISE *measures* conciseness post-hoc; it does not *intervene* at decoding time. That is precisely our contribution slot.

---

**Paper 2 — Semantic-Eval** ✅ VERIFIED
*"Semantic-Eval: A Semantic Comprehension Evaluation Framework for Large Language Models Generation without Training"*, Li et al., ACL 2025 (Long), pp. 9675–9690. https://aclanthology.org/2025.acl-long.477/ · Code: https://github.com/LssTry/Semantic-Eval

What it does: a training-free framework for evaluating semantic comprehension of LLM-generated text; evaluated across 8 datasets / 4 tasks; reported to surpass n-gram and BERT-based metrics in correlation with human judgment, slightly below GPT-4-as-judge.

**Read it to answer:**

1. How do they compute semantic similarity, at what granularity (token / sentence / segment), and with which encoders?
2. What can we reuse for our **semantic redundancy module** (measuring overlap between generated segments) — and what is too heavy for a decoding loop and belongs only in *evaluation*? Keep this distinction sharp: evaluation-time machinery may be expensive; decoding-time machinery must be lightweight.
3. How do they validate against human judgment (correlation statistics used)?
4. **Eman verifies the repo runs this week** — clone it; check whether the code actually runs and what it needs.

---

**Paper 3 — Speculative Speculative Decoding** (confirmed assigned reading)
Kumar, Dao & May, "Speculative Speculative Decoding," arXiv:2603.03251 (Mar 2026). https://arxiv.org/abs/2603.03251

Parallelizes the speculate/verify steps of standard speculative decoding by having the draft model pre-emptively predict verification outcomes.

**Read it for:** (a) how a decoding-time intervention is formalized mathematically; (b) the *distribution-preservation* discipline (inspiration for our zero-weights identity invariant); (c) how such papers structure their evaluation and claims.

> **Note on citation accuracy:** This is a distinct, newer paper that extends the foundational mechanism in Leviathan et al. (arXiv:2211.17192, ICML 2023), which is the paper already analyzed in the Track-B Master Plan. Both are legitimate citations depending on the point being made — don't conflate them in the bibliography.

---

**Paper 4 — Human evaluation reference** (resolved from ⚠️ UNCERTAIN)
Chiang & Lee, "Can Large Language Models Be an Alternative to Human Evaluations?" ACL 2023, arXiv:2305.01937. https://arxiv.org/abs/2305.01937

**Read it for:** conditions under which an LLM-judge is/isn't a valid substitute for human annotation — directly informs Decision 2 (Section 9) and the verbosity-bias risk (Section 12).

---

### 6.2 The 12-Paper Hunt (3 per member) — Search Protocol

**Inclusion criteria (apply to every candidate):** (1) peer-reviewed venue or widely-cited preprint; (2) you can state in one sentence what it contributes *to our paper* (definition, method, metric, or evidence); (3) published 2016+ unless it is a foundational metric/method paper; (4) you have actually read at least: abstract, intro, method figure, evaluation setup, limitations.

**Where to search:** ACL Anthology (aclanthology.org — filter by venue/year), Semantic Scholar, Google Scholar, arXiv (cs.CL). For each topic below: run the queries, snowball from the reference lists of ConCISE and Semantic-Eval, and check who *cites* ConCISE (Semantic Scholar "citations" tab) — a young paper's citers are often the most current related work.

| Topic                                            | Owner   | Queries                                                                                                                                                                                    | Deliverable framing                                                                                                                                                                   |
| ------------------------------------------------ | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Verbosity in LLMs**                      | Mahmoud | "verbosity bias LLM", "length bias LLM evaluation", "LLM over-explanation", "length bias RLHF", "concise response generation LLM"                                                          | Evidence that (i) LLMs systematically over-generate and (ii) evaluators/judges reward length — this is the empirical backbone of the Introduction                                    |
| **Redundancy reduction in generated text** | Elsayed | "redundancy reduction text generation", "repetition penalty neural text generation", "n-gram blocking decoding", "degeneration repetition language model", "self-repetition summarization" | Which lexical-redundancy detectors exist, which are usable*inside* a decoding loop at O(cheap) cost, and what they miss (semantic paraphrase redundancy → motivates Eman's signal) |
| **Over-generation in dialogue systems**    | Eman    | "over-generation dialogue systems", "response length control dialogue", "informativeness vs verbosity dialogue", "Gricean maxims dialogue generation quantity"                             | The*communication-theoretic* grounding for why extra content harms understanding — Grice's Maxim of Quantity gives the theoretical anchor LUHME reviewers will appreciate          |
| **Conversational alignment in LLMs**       | Mirna   | "conversational alignment LLM", "common ground human-AI dialogue", "alignment lexical entrainment dialogue", "perceived understanding conversational agents"                               | What "alignment" means measurably, so our claim "verbosity weakens alignment" is testable rather than rhetorical                                                                      |

**🔎 LEAD — VERIFY BEFORE CITING** (per topic):

- **Topic A (Mahmoud):** work on verbosity bias in preference labeling / LLM-as-judge (known finding around the MT-Bench line of work); work on length correlations in RLHF reward models; recent "overthinking"/CoT-length reduction literature.
- **Topic B (Elsayed):** the neural-text-degeneration literature (repetition loops), unlikelihood-training line (note: training-based → related-work only), decoding-time repetition controls (directly our lineage).
- **Topic C (Eman):** pre-LLM NLG over-generation literature (over-generate-and-rank pipelines — note different sense of the term; distinguish carefully); NLP papers that operationalize Gricean Maxims.
- **Topic D (Mirna):** the common-ground survey **in LUHME 2025 itself** (Anikina et al., "Building Common Ground in Dialogue: A Survey", https://aclanthology.org/2025.luhme-1.2/ — ✅ verified to exist; citing the venue's own relevant work is both intellectually honest and strategically sensible); psycholinguistic alignment theory (interactive alignment) and its NLP operationalizations.

---

### 6.3 Reading Template (one per paper — commit to `/reading/<topic>/<firstauthor_year>.md`)

```markdown
# [Title], [Authors], [Venue Year], [URL]
Verified: [what you checked: abstract/PDF/code] on [date]
1. Claim (one falsifiable sentence):
2. Method (2–3 sentences, mechanism-level):
3. Evaluation (data, metrics, human eval? agreement stats?):
4. Result that matters to us (number + condition, exactly as printed):
5. What WE take from it (definition / metric / baseline / evidence / framing):
Risks/objections a reviewer could raise using this paper against us:
BibTeX: (paste from ACL Anthology / arXiv — never hand-type)
```

The master plan's rule applies: every bullet a standalone, falsifiable claim. No vibes.

---

## 7. Overleaf — Paper Skeleton & Continuous Writing

Supervisor's rule: **write continuously, from day one**. Every reading, observation, and experiment lands in Overleaf the day it happens (as draft text or a `\todo{}`/comment), not at the end.

### 7.1 Skeleton (ACL template, targeting ≤8 pages; Limitations + Ethics + References are free)

Mirrors the actual LaTeX structure in `docs/paper-definition/peper-template.tex`. Each numbered section has a corresponding markdown file at `docs/paper-definition/` for section-by-section drafting.

```
Abstract (uncounted)                     — team (150–250 words; scaffold in peper-template.tex ll.95–108)
1. Introduction                          (~1.0 p)  — Mahmoud       → 01-introduction.md
2. Related Work                          (~1.25 p) — all four      → 02-related-work.md
    2.1 Verbosity & length biases in LLMs            (Mahmoud)
    2.2 Redundancy reduction & repetition control     (Elsayed)
    2.3 Over-generation in dialogue systems           (Eman)
    2.4 Conversational alignment & human-centered eval (Mirna)
    2.5 Decoding-time intervention (brief positioning) (Mahmoud)
3. Problem Formulation                   (~0.75 p) — team          → 03-problem-formulation.md
   (operational definitions: verbosity, lexical redundancy, semantic redundancy,
    and the hypothesis linking them to clarity/alignment)
4. Verbosity-Aware Decoding (Method)     (~1.5 p)  — Elsayed+Eman  → 04-verbosity-aware-decoding.md
    4.1 Three verbosity signals (L_t, R_t, S_t)
    4.2 Entropy gate (g(H_t))
    4.3 Invariants (zero-weights, EOS-only, entropy gate, stateless)
    4.4 Scope for this paper (single model, dataset, greedy decoding)
5. Experimental Setup                    (~1.0 p)  — Mahmoud+Eman  → 05-experimental-setup.md
6. Evaluation Protocol & Results         (~1.75 p) — Mirna (+ all) → 06-evaluation-protocol-and-results.md
    6.1 Automatic metrics
    6.2 Human evaluation
    6.3 Results
7. Discussion                            (~0.5 p)  — team          → 07-discussion.md
Limitations (uncounted)                  — team                    → 08-limitations.md
Ethics Statement (uncounted)             — Mirna                   → 09-ethics-statement.md
Appendix: Human Evaluation Instrument    — Mirna                   → 10-appendix-human-evaluation-instrument.md
```

### 7.2 Introduction Scaffold (structure only — the TEAM writes the actual argument; per Dr. Ferdousi, interpretation is yours, not a tool's)

Paragraph-by-paragraph plan; fill each with your own prose + citations from the Phase-1 reading:

1. **Phenomenon:** LLMs frequently produce responses longer and more redundant than the communicative goal requires. [cite Topic-A evidence + ConCISE's motivation]
2. **Why it matters — as communication, not cost:** excess content increases ambiguity, buries the informative core, and degrades the user's ability to extract meaning → weaker human–AI understanding and conversational alignment. [cite Topic-C/D grounding; Gricean Quantity if adopted]
3. **Why existing answers are insufficient:** prompting "be concise" is unreliable; post-hoc summarization/truncation discards or damages content after generation; training-based compression changes the model. Gap: *decoding-time*, training-free control that shapes what is generated in the first place.
4. **Our hypothesis (state it falsifiably):** e.g., "Responses generated under verbosity-aware decoding are rated significantly higher in clarity and perceived understanding, and lower in redundancy, at equal task success / semantic completeness." ← Day-3 team wording session (Decision 3).
5. **Contributions (3 bullets, each measurable):** (i) an operational, communication-grounded formulation of verbosity/redundancy for decoding; (ii) a training-free verbosity-aware decoding method (composite gated logit reshaping); (iii) a human-centered evaluation protocol (clarity, usefulness, redundancy, perceived understanding) + automatic conciseness/semantic-preservation metrics, with results on [dataset].

### 7.3 Overleaf Hygiene

- One `.tex` file per section; `refs.bib` is append-only and every entry pasted from ACL Anthology/arXiv (no hand-typed BibTeX).
- Use `\todo{}` comments liberally; a section with visible holes beats an empty section.
- Never paste text you have not verified against the source you cite.

---

## 8. Methodology Sketch (Week-1 Deliverable #3)

**Mechanism (unchanged from master plan §3; restated here so this file is self-contained):** at each decoding step, modify logits before selection:

```
Z̃_t(v) = Z_t(v) − g(H_t) · [ w_L·L_t(v) + w_R·R_t(v) + w_S·S_t(v) ]
```

- `L_t(v)`: length-aware EOS encouragement — non-zero **only** at `v = <EOS>` (uniform shifts cancel under softmax: softmax(z + c·1) = softmax(z); this was Algorithm Correction 1).
- `R_t(v)`: n-gram repetition penalty — only tokens completing an already-seen k-gram (Elsayed's workstream refines this).
- `S_t(v)`: semantic redundancy penalty on top-K candidates — similarity of candidate to committed output history (Eman's workstream decides the representation: unembedding rows vs. sentence embeddings; tradeoff = in-distribution & cheap vs. semantically richer & heavier).
- `g(H_t) ∈ [0,1]`: entropy gate — full penalty when the model is confident (likely filler), no penalty when uncertain (likely content). Multiplicative, never additive (Algorithm Correction 2).
- **Invariants (fixed — do not change):** zero-weights identity; EOS-only length term; entropy as gate; stateless from `input_ids`. These are hard constraints.

**What the LUHME framing changes (and only this):**

1. **Motivation of each term is stated in communication terms.** R targets *lexical* redundancy (verbatim re-saying), S targets *semantic* redundancy (paraphrased re-saying), L targets *structural* over-continuation (talking past the point of completion). Map each to the harm it causes a listener; if the team adopts the Gricean framing, each term operationalizes a violation of the Maxim of Quantity. ← This mapping is a team-discussion output for Phase 2, not settled here.
2. **Success is defined by human-centered outcomes** (Section 10), not TRR. Length reduction is reported descriptively, not as the headline.
3. **Scope discipline for an 8-page workshop paper:** one primary model (Mistral-7B-Instruct-v0.2, per master plan §2.1 — fits free Colab T4 in 4-bit NF4), one dataset (Section 10.2 decision), greedy/deterministic decoding, 2–3 lightweight baselines: (a) unmodified decoding, (b) "please be concise" prompting, (c) HF `repetition_penalty` / `no_repeat_ngram_size`. Cross-model validation and beam-search tracks belong to Track B, not this paper.
4. LazyLLM / SlimInfer / DIP: **omit or one sentence** in Related Work 2.5. They are input-side/prefill methods; in the LUHME framing they are barely relevant, and treating them as baselines would be a category error in *any* framing.

**Open methodological questions to resolve as a team (bring positions to Phase 2):**

- Q1: Semantic signal representation — unembedding-row cosine (cheap, in-distribution, ~0 infra) vs. sentence-embedding cosine over a sliding window (richer, heavier, needs an encoder in the loop). Criteria: per-step overhead budget (<5%), and which better matches human redundancy judgments on a 20-example pilot.
- Q2: Are Atlas/entropy-gate calibration diagnostics in-scope for the workshop paper, or Track-B material? (Tradeoff: interpretability story vs. page budget and time.)
- Q3: Instruction data is open-ended (no gold reference) — so "semantic completeness" must be checked reference-free (LLM-judge with length-debiasing, or human "did it answer the question?" item). Decide which.

---

## 9. Decisions to Close — Meeting Agenda for Phase 2 (Jul 6)

These are decisions for the **team and supervisor** — not analysis for any tool to resolve.

| # | Decision                                                                                                                                                       | Why it's urgent                                                                          |
| - | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 1 | Dataset: AlpacaEval vs. MT-Bench (brief: Section 10.2)                                                                                                         | Blocks prompt selection, baseline generation, evaluation design                          |
| 2 | Human-eval execution model: team-internal raters vs. LLM-judge (length-controlled) as primary evidence                                                         | Largest schedule risk; determines whether GREB ethics review is triggered (Section 10.3) |
| 3 | Falsifiable hypothesis wording (Section 7.2, item 4)                                                                                                           | Blocks Introduction v1                                                                   |
| 4 | Paper title — 3 to 5 candidates (keep "Say Less, Mean More: ..." as one candidate and generate LUHME-framed alternatives emphasizing understanding/alignment) | Explicitly requested by the supervisor                                                   |
| 5 | Semantic-signal representation: unembedding-row cosine vs. sentence-embedding cosine (Section 8,`S_t`)                                                       | Affects per-step compute budget (<5% target) and Eman's implementation start date        |
| 6 | Task ownership by name/date beyond Phase 2 (Phase 3 onward)                                                                                                    | Execution cannot start without it                                                        |

---

## 10. Evaluation Metrics & Dataset (Week-1 Deliverables #4 and #5)

### 10.1 Candidate Metric List (Mirna curates; team prunes Phase 2)

**Automatic — verbosity/redundancy side:**

| Metric                                               | Measures                              | Cost               | Notes / risks                                                      |
| ---------------------------------------------------- | ------------------------------------- | ------------------ | ------------------------------------------------------------------ |
| Response length (tokens, sentences)                  | Raw verbosity                         | free               | Descriptive only; never a quality claim by itself                  |
| Length ratio vs. baseline (paired)                   | Effect of intervention                | free               | Paired per-prompt; report distribution, not just mean              |
| Distinct-n / repetition rate / duplicate-phrase rate | Lexical redundancy                    | free               | 🔎 verify canonical citations for distinct-n before citing         |
| Inter-segment embedding similarity                   | Semantic redundancy within a response | cheap              | Directly reuses Eman's module; define segmentation rule explicitly |
| ConCISE score                                        | Conciseness (reference-free)          | LLM calls per item | ✅ verified metric; budget the calls; report which LLM backs it    |

**Automatic — meaning-preservation side (the "at no loss of content" half of the claim):**

| Metric                                            | Measures                                | Notes                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BERTScore-F1 (concise output vs. baseline output) | Semantic preservation across conditions | Record scorer model name in every table (master-plan rule)                                                                                                                                                                                                                                                                                         |
| Semantic-Eval framework                           | Semantic comprehension quality          | ✅ verified; Eman checks runnability this week                                                                                                                                                                                                                                                                                                     |
| LLM-as-judge pairwise (length-debiased)           | Overall preference at controlled length | ⚠️ Judges systematically favor longer outputs (verbosity bias — Mahmoud's Topic-A reading documents this). Any judge-based comparison MUST use a length-controlled protocol, or it is invalid for a verbosity paper. Pre-register the protocol before seeing results (master-plan discipline). Reference: Dubois et al. 2024, arXiv:2404.04475. |

**Human evaluation (the headline for LUHME) — supervisor's four dimensions:**

- **Clarity** — "How easy was it to understand what this response is saying?" (Likert 1–5, anchored)
- **Usefulness** — "How well does the response serve the request?" (Likert 1–5)
- **Redundancy** — "How much content is repeated or unnecessary?" (Likert 1–5, reversed)
- **Perceived understanding** — "Does the system seem to have understood the request?" (Likert 1–5)
- Plus a **pairwise A/B**: "Which response communicates better?" (baseline vs. ours, order randomized, length visible? — decide and pre-register)
- **Agreement statistics required:** report inter-annotator agreement (e.g., Krippendorff's α or Cohen's/Fleiss' κ) — the LUHME 2025 LLM-judge paper shows this venue scrutinizes evaluation methodology.
- **Statistical tests:** paired, per-prompt design → Wilcoxon signed-rank + bootstrap 95% CI + effect size (rank-biserial r). Same standard as the master plan §7.3 — a mean difference alone is not a result.
### 10.2 Dataset Decision Brief — AlpacaEval vs. MT-Bench vs. YapBench

| Criterion | **AlpacaEval** | **MT-Bench** | **YapBench** |
|---|---|---|---|
| What it is | ~805 single-turn instructions with an automatic judge protocol; v2 introduced a **length-controlled win rate** specifically because judges favor longer outputs (Dubois et al. 2024, arXiv:2404.04475 — verified) | 80 multi-turn (2-turn) questions across 8 categories, LLM-judge scored; introduced alongside Chatbot Arena (Zheng et al. 2023, NeurIPS 36 — verified) | 300+ single-turn prompts across 3 brevity-ideal categories (ambiguous-input clarification, closed-form factual Q&A, one-line coding). Each item has a curated minimal-sufficient reference answer + category tag. Metric: YapScore (excess length vs. reference, in characters — tokenizer-agnostic), rolled up per model as YapIndex. 76 LLMs benchmarked at release; public leaderboard (Borisov et al., 2026, arXiv:2601.00624 — verified) |
| Fit to "conversational alignment" framing | Weaker — single-turn, no dialogue | Stronger — genuinely multi-turn; alignment/turn-taking story is more natural | Weakest — single-turn only, no dialogue, and no built-in clarity/alignment judgment at all; YapScore is a pure length-vs.-reference measurement, not a human- or judge-rated communication signal. Any clarity/usefulness/perceived-understanding claim needs a separate instrument layered on top, same as the other two |
| Statistical power | Stronger — hundreds of prompts → paired tests well-powered | Weaker — n=80 items; human-eval subset even smaller | n > 300 — between the other two. Because YapScore compares to a fixed per-item reference rather than a judge/preference call, it likely needs less averaging to detect an effect on the verbosity axis specifically |
| Verbosity relevance | Very high — the length-controlled metric exists because of exactly the bias we study; we can *use* their debiasing protocol | High — the verbosity bias of judges is documented in this line of work | Highest — purpose-built for exactly this phenomenon, with a tokenizer-agnostic reference metric and documented category-specific failure modes (e.g., filling in unwarranted content on ambiguous prompts, over-explaining one-line coding asks) that map fairly directly onto the L_t/R_t/S_t terms. Its own motivation leans on "cognitive load," not just token cost — arguably closer to our communication framing than AlpacaEval's/MT-Bench's judge-preference framing |
| Human-eval cost | Must subsample (e.g., 100–150 prompts × 2 systems) | Small enough to rate exhaustively | Zero for the verbosity axis — YapScore is fully automatic, no LLM judge or human rater involved. Doesn't reduce the cost of the clarity/usefulness/redundancy/perceived-understanding ratings, though — those stay the headline evidence regardless of which set is chosen |
| Risk | Judge-based metrics dominate its ecosystem → we must not let LLM-judge replace human eval | Small n → significance harder; category confounds | Narrow scope — three brevity-ideal prompt types only, which may exercise R_t/S_t (redundancy across longer generations) far less than open-ended instructions would. Released Jan 2026 — no citation track record yet, so a LUHME reviewer is less likely to recognize it. Also a units mismatch to flag: YapScore is character-based, not token-based |

**Possible resolutions to discuss (present to Dr. Ferdousi; do not pre-decide):** (a) MT-Bench as the primary set (framing fit) + AlpacaEval subset for power; (b) AlpacaEval primary (power + length-controlled tooling) with the alignment claim scoped to "instruction-following interactions"; (c) **MT-Bench + YapBench** — the second package Dr. Ferdousi offered directly: MT-Bench carries the human-centered hypothesis test, and YapBench serves as an automatic, reference-based construct-validity check on whatever verbosity metric the team reports (does a reduction on MT-Bench track with reduced YapScore overshoot on YapBench's fixed prompts?) — not as a replacement primary corpus, since its category scope is narrower and its metric is unit-different from anything token-based. Decision criteria: which claim do we most want the paper to make, and what human-annotation budget do we actually have?
### 10.3 ⚠️ Human-Subjects Question — Raise with the Supervisor NOW, Not Later

If annotators are anyone beyond the research team, Queen's likely requires research-ethics review (GREB), which has lead time. **Ask Dr. Ferdousi on Day 1–2:** who will the annotators be (team-internal, recruited students, crowdworkers?), and is ethics approval needed for the intended design? Given 11 days total, default to **team-internal raters** unless the supervisor confirms an already-approved protocol. (Status: OPEN QUESTION — we have not verified Queen's policy; do not assume either way.)

---

## 11. End-of-Phase Deliverables — Supervisor's Checklist

| #  | Dr. Ferdousi expects                             | Our artifact                                                                                               | Owner                   |
| -- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | ----------------------- |
| 1  | Clear literature summary from each member        | 4 × (3 topic papers + core-paper templates) in`/reading/` + one condensed `/reading/week1_summary.md` | each member             |
| 2  | Rough problem statement in Overleaf              | §3 Problem Formulation v0 (operational definitions + falsifiable hypothesis)                              | team (Phase-2 sessions) |
| 3  | Proposed methodology sketch                      | §4 Method v0 (Section 8 of this plan, written as paper prose)                                             | Elsayed + Eman          |
| 4  | Candidate evaluation metrics list                | §6 Evaluation v0 + metrics tables (Section 10.1)                                                          | Mirna                   |
| 5  | Initial dataset discussion                       | Decision brief (Section 10.2) as a one-pager + Overleaf comment                                            | Mahmoud + Eman          |
| — | (from email) submission requirements familiarity | Section 2 of this file + OpenReview accounts live                                                          | Mahmoud                 |
| — | (from email) previous proceedings studied        | 8 proceedings summaries in`/reading/luhme_proceedings/`                                                  | all                     |

---

## 12. Weekly Update Email (send every week, unprompted — she asked)

> Subject: MinimalLM / LUHME 2026 — Week 1 update
> Dear Dr. Ferdousi,
> This week: (1) submission requirements confirmed — ACL template, ≤8 pp, double-blind, OpenReview, deadline **July 15**; (2) proceedings studied — key takeaways: [2 lines]; (3) core papers read (ConCISE, Semantic-Eval, Speculative Speculative Decoding, Chiang & Lee) — summaries in the repo; (4) 12 topic papers collected: [counts per topic]; (5) Overleaf now contains: Introduction v0, Problem Formulation v0, Method v0, Evaluation v0.
> Decisions we would like your input on at our Jul 6 meeting: title candidates, dataset choice (brief attached), human-eval annotators & ethics.
> Next week we plan: [3 bullets].
> Best regards, [team]

---

## 13. Risk Register

| Risk                                                         | Likelihood       | Impact                    | Mitigation                                                                                          |
| ------------------------------------------------------------ | ---------------- | ------------------------- | --------------------------------------------------------------------------------------------------- |
| Human-eval ethics (GREB) approval lead time                  | Medium           | High                      | Resolve Decision 2 at Phase 2; default to team-internal raters absent an existing approved protocol |
| LLM-judge verbosity bias invalidates a comparison            | High if ignored  | High                      | Length-controlled protocols only (Dubois et al. 2024); human eval remains primary; pre-register     |
| Scope creep (multi-model, multi-dataset, Atlas, beam search) | High             | High                      | Workshop scope locked in Section 8; everything else → Track B                                      |
| Two framings (efficiency vs. communication) bleed together   | Medium           | High (reviewer confusion) | Section 1 table; Mahmoud checks every Overleaf commit against it                                    |
| Semantic signal too slow in the decode loop                  | Medium           | Medium                    | <5% per-step overhead budget; top-K + every-k-steps computation; unembedding-row fallback           |
| OpenReview profile activation delays                         | Low              | Medium                    | Accounts created Phase 1 with institutional emails                                                  |
| **11-day timeline slips**                              | **Medium** | **Critical**        | **Phase 2 meeting is a hard gate — Decisions 1–6 must close Jul 6, no extensions**          |

---

## Appendix A — Core Method Invariants (Unchanged by Framing)

- **Zero-weights identity** — with all penalty weights = 0, output must be bit-identical to the unmodified baseline.
- **EOS-only length term** — length pressure touches only the `<EOS>` logit, never a uniform shift across the vocabulary (softmax is shift-invariant, so a uniform shift is a mathematical no-op).
- **Entropy as a multiplicative gate** — entropy scales the penalty; never added directly to logits, same shift-invariance reasoning.
- **Stateless from `input_ids`** — no mutable running state that beam reordering could corrupt.

---

## Appendix B — Verified BibTeX

```bibtex
@misc{ghafari2025concise,
  title  = {ConCISE: A Reference-Free Conciseness Evaluation Metric for LLM-Generated Answers},
  author = {Ghafari, Seyed Mohssen and others},
  year   = {2025},
  eprint = {2511.16846},
  archivePrefix = {arXiv}
}

@inproceedings{li-etal-2025-semantic-eval,
  title     = {Semantic-Eval: A Semantic Comprehension Evaluation Framework for Large Language Models Generation without Training},
  author    = {Li, Shusheng and Li, Jiale and Qu, Yifei and Shi, Xinwei and Guo, Yanliang and He, Ziyi and Wang, Yubo and Tan, Wenjun},
  booktitle = {Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  year      = {2025}, address = {Vienna, Austria},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2025.acl-long.477/},
  doi       = {10.18653/v1/2025.acl-long.477}, pages = {9675--9690}
}

@misc{kumar2026speculativespeculativedecoding,
  title  = {Speculative Speculative Decoding},
  author = {Kumar, Tanishq and Dao, Tri and May, Avner},
  year   = {2026},
  eprint = {2603.03251},
  archivePrefix = {arXiv},
  primaryClass = {cs.LG}
}

@inproceedings{chiang-lee-2023-alternative,
  title     = {Can Large Language Models Be an Alternative to Human Evaluations?},
  author    = {Chiang, Cheng-Han and Lee, Hung-yi},
  booktitle = {Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  year      = {2023},
  publisher = {Association for Computational Linguistics}
}

@misc{dubois2024lengthcontrolled,
  title  = {Length-Controlled AlpacaEval: A Simple Way to Debias Automatic Evaluators},
  author = {Dubois, Yann and Galambosi, Bal{\'a}zs and Liang, Percy and Hashimoto, Tatsunori B.},
  year   = {2024},
  eprint = {2404.04475},
  archivePrefix = {arXiv}
}

@inproceedings{zheng2023judging,
  title     = {Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena},
  author    = {Zheng, Lianmin and others},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {36},
  year      = {2023}
}

% Note: Leviathan, Kalman, Matias (arXiv:2211.17192, ICML 2023) — the foundational
% Speculative Decoding paper — is Track-B/Master-Plan material, not the LUHME-assigned
% reading (that is Kumar/Dao/May above). Keep the two citations distinct.
```

---

*This document consolidates verified facts from both prior plans into a single execution plan. The decisions in Section 9 are to be finalized by the team and the supervisor, not resolved here.*
