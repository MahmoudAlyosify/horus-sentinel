# Claude Code + Cursor Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install Claude Code CLI, guide Cursor extension setup, and add a committed root `CLAUDE.md` so Claude Code can generate code for HORUS Sentinel inside Cursor.

**Architecture:** Machine-local Claude Code CLI (native Windows installer) plus the official Cursor extension (`anthropic.claude-code`) share Anthropic auth. Project context lives in git-root `CLAUDE.md`, which points agents at the nested Python package `horus-sentinel/`. No application runtime LLM changes.

**Tech Stack:** Claude Code CLI, Cursor IDE extension `anthropic.claude-code`, PowerShell, git, existing Python app under `horus-sentinel/` (pytest, ruff, uvicorn) unchanged.

## Global Constraints

- Windows 10+; this workspace is PowerShell-first.
- Paid Claude plan (Pro / Max / Team / Enterprise) or Anthropic API billing required; Free Claude.ai is insufficient.
- Do **not** modify `horus_brain/`, agents, API routes, or add Anthropic SDK to the app for this plan.
- Do **not** create `.claude/settings.json` in v1 (out of scope per spec).
- Do **not** modify or delete anything under `horus-sentinel/horus-geointel/`.
- Do **not** commit `.env`, API keys, or credentials.
- Prefer native installer `irm https://claude.ai/install.ps1 | iex` over WinGet (WinGet is fallback only).
- `CLAUDE.md` path is exactly `CLAUDE.md` at git root (sibling of nested `horus-sentinel/` package and `docs/`).
- Keep `CLAUDE.md` to roughly one–two screens; no novel essays.

---

### Task 1: Install and verify Claude Code CLI

**Files:**
- Create: none (machine PATH / installer only)
- Modify: none
- Test: shell verification commands below

**Interfaces:**
- Consumes: network; PowerShell execution policy allowing remote scripts for the installer
- Produces: `claude` executable on PATH; version string printable via `claude --version`

- [ ] **Step 1: Check whether CLI is already installed**

Run (PowerShell):

```powershell
where.exe claude 2>$null
if ($LASTEXITCODE -ne 0) { Write-Output "claude not on PATH" } else { claude --version }
```

Expected: either a version line (skip to Step 4) or `claude not on PATH`.

- [ ] **Step 2: Run the native Windows installer**

Run (PowerShell, not x86-only host if avoidable):

```powershell
irm https://claude.ai/install.ps1 | iex
```

Expected: installer completes without fatal error. If script execution is blocked, set process-scoped policy then retry:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
irm https://claude.ai/install.ps1 | iex
```

Fallback only if native install fails:

```powershell
winget install Anthropic.ClaudeCode
```

- [ ] **Step 3: Refresh PATH in a new shell**

Close the current terminal tab and open a new one in Cursor (or start a new PowerShell). Do not assume the old session sees the new PATH.

- [ ] **Step 4: Verify CLI**

Run:

```powershell
claude --version
```

Expected: a version string (e.g. containing digits/semver). If `claude` is still not found, inspect user PATH for the Anthropic install directory, fix PATH, and re-open the terminal.

- [ ] **Step 5: Commit**

No repo files changed. Skip commit for this task.

---

### Task 2: Authenticate Claude Code CLI

**Files:**
- Create: none (credentials live in user Claude Code config under the home directory)
- Modify: none
- Test: interactive `claude` session

**Interfaces:**
- Consumes: working `claude` from Task 1; paid Anthropic/Claude account
- Produces: authenticated CLI session usable by the Cursor extension later

- [ ] **Step 1: Start Claude Code from the git root**

```powershell
cd c:\Users\DPQUSD250122\Desktop\horus_sentinel\horus-sentinel
claude
```

Expected: browser auth prompt on first run, or an interactive Claude Code prompt if already logged in.

- [ ] **Step 2: Complete browser login**

Sign in with the account that has Claude Code entitlement. Return to the terminal when the CLI confirms authentication.

If auth fails: verify plan tier, org policy, and that the region is supported by Anthropic. Do not proceed to invent app-side API keys for this plan.

- [ ] **Step 3: Smoke-prompt in CLI (optional but recommended)**

In the Claude Code session, ask:

```text
Reply with exactly: CLAUDE_CODE_OK
```

Expected: response contains `CLAUDE_CODE_OK`. Exit the session (`/exit` or Ctrl+C per Claude Code UI).

- [ ] **Step 4: Commit**

No repo files changed. Skip commit.

---

### Task 3: Add committed project `CLAUDE.md`

**Files:**
- Create: `CLAUDE.md` (git root)
- Modify: none
- Test: content checklist + `pytest` smoke from package dir (proves app untouched)

**Interfaces:**
- Consumes: product facts from `horus-sentinel/README.md`, frozen-folder rule from `horus-sentinel/AGENT_HANDOFF.md` / README
- Produces: root `CLAUDE.md` read by Claude Code on every session in this repo

- [ ] **Step 1: Write `CLAUDE.md` with this exact content**

Create `c:\Users\DPQUSD250122\Desktop\horus_sentinel\horus-sentinel\CLAUDE.md`:

````markdown
# HORUS Sentinel — Claude Code guide

Autonomous, **passive** multi-agent OSINT / threat-intelligence platform (ITC-Egypt 2026).
Specialized agents collect public intel, ground it in a knowledge graph + RAG, and a
self-hosted HORUS brain authors evidence-backed reports. Humans validate before anything is final.

## Repo layout

- **Git root (this folder):** docs, pitch materials, and this `CLAUDE.md`.
- **Application package:** `horus-sentinel/` — FastAPI API, agents, tools, graph, RAG, `horus_brain/`, UI, tests, deploy.

When running or testing application code, `cd horus-sentinel` first.

## Commands (from `horus-sentinel/`)

```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements-dev.txt
uvicorn api.main:app --reload                    # UI http://localhost:8000/ui
pytest                                           # offline-friendly suite
ruff check . && ruff format --check .
```

Full stack (optional): `docker compose -f deploy/docker-compose.yml up -d` from `horus-sentinel/`.

## Conventions

- Prefer existing patterns in `agents/`, `api/`, `horus_brain/`, `core/`, `tools/`.
- Keep changes small and focused; match local style (ruff).
- Brain transports today: HF / Ollama / offline synthesis via `horus_brain/brain.py`. Do not swap the product brain to Claude API unless explicitly requested as an app feature.
- Optional services degrade gracefully; prefer code that works offline when possible.

## Safety / do not

- Platform is **passive and defensive**. Do not add unauthorized active recon, exploitation, or attacks on third-party infrastructure. See `horus-sentinel/RESPONSIBLE_USE.md`.
- Never commit secrets: `.env`, API keys, tokens, credentials.
- **`horus-sentinel/horus-geointel/` is FROZEN** — do not modify, fabricate, or delete it. Build around it.
````

- [ ] **Step 2: Verify file exists at git root**

```powershell
Get-Item .\CLAUDE.md | Select-Object FullName, Length
```

Expected: path ends with `\horus-sentinel\CLAUDE.md` and Length > 0.

- [ ] **Step 3: Smoke-check application tests still pass (no app edits)**

```powershell
cd horus-sentinel
pytest -q
```

Expected: suite passes (or same baseline as before this task). If failures appear and you did not touch Python, stop and report — do not “fix” unrelated app bugs in this plan.

- [ ] **Step 4: Commit**

```powershell
cd c:\Users\DPQUSD250122\Desktop\horus_sentinel\horus-sentinel
git add CLAUDE.md
git commit -m "Add CLAUDE.md for Claude Code project context."
```

Expected: clean commit containing only `CLAUDE.md`.

---

### Task 4: Install Claude Code extension in Cursor (user + agent checklist)

**Files:**
- Create: none in repo
- Modify: none in repo (Cursor user extensions)
- Test: extension visible + panel opens

**Interfaces:**
- Consumes: Cursor IDE; same Anthropic account as Task 2
- Produces: Claude Code panel (✦) available in this workspace

- [ ] **Step 1: Open Extensions in Cursor**

Press `Ctrl+Shift+X`. Search for exactly: `Claude Code`.

- [ ] **Step 2: Install official extension**

Install **Claude Code** published by Anthropic, extension ID `anthropic.claude-code`.

If marketplace search fails, open Anthropic’s “Install for Cursor” link from https://code.claude.com/docs/en/ide-integrations and complete install. Fallback: CLI-only workflow from Task 1–2 still satisfies partial success; document the failure.

- [ ] **Step 3: Open the Claude Code panel**

Use one of: spark (✦) icon on an editor, status-bar “Claude Code”, or Command Palette → “Claude Code”.

Expected: chat panel opens. Sign in if prompted (should reuse CLI auth when available).

- [ ] **Step 4: Reload if broken**

If the panel errors after install or after a Cursor update: Command Palette → `Developer: Reload Window`. If still broken, use integrated terminal `claude` until the extension works.

- [ ] **Step 5: Commit**

No repo files. Skip commit.

---

### Task 5: End-to-end acceptance

**Files:**
- Create: none
- Modify: none
- Test: acceptance checklist from the design spec

**Interfaces:**
- Consumes: Tasks 1–4 complete; `CLAUDE.md` present
- Produces: confirmed dual-path coding setup (CLI + extension)

- [ ] **Step 1: CLI version check**

```powershell
claude --version
```

Expected: version printed.

- [ ] **Step 2: Extension panel check**

Open Claude Code panel in Cursor on this repo. Expected: panel loads without crash.

- [ ] **Step 3: Project-context check**

In either the extension panel or `claude` CLI (cwd = git root), ask:

```text
What is this project, where is the Python package, and what command runs tests?
```

Expected answer (substance, not exact wording):

- HORUS Sentinel / passive OSINT platform
- Package under `horus-sentinel/`
- Tests via `pytest` from that directory

- [ ] **Step 4: Confirm non-goals**

Verify `git status` shows no unintended changes under `horus-sentinel/api`, `horus-sentinel/agents`, or `horus-sentinel/horus_brain` from this work.

```powershell
cd c:\Users\DPQUSD250122\Desktop\horus_sentinel\horus-sentinel
git status -sb
```

Expected: clean tree or only intentional docs/`CLAUDE.md` commits already made; no brain/API churn.

- [ ] **Step 5: Commit**

No further commit unless acceptance notes were requested as docs (not in this plan). Skip.

---

## Spec coverage (self-review)

| Spec requirement | Task |
|------------------|------|
| Native CLI install + version verify | Task 1 |
| Auth / shared account | Task 2 |
| Cursor extension `anthropic.claude-code` | Task 4 |
| Root `CLAUDE.md` with product, layout, commands, conventions, safety, frozen folder | Task 3 |
| No app brain / Anthropic-in-app | Global Constraints + Task 5 Step 4 |
| Acceptance criteria 1–5 | Task 5 (+ pytest in Task 3) |
| WinGet / reload / marketplace fallbacks | Tasks 1, 4 |
| No `.claude/settings.json` v1 | Global Constraints |

## Placeholder / consistency check

- No TBD/TODO left in steps.
- Paths use git root `CLAUDE.md` and package `horus-sentinel/` consistently (spec’s `horus-sentinel/horus-sentinel/` wording maps to Desktop wrapper + git root + package; implementers use paths in this plan).
