# Claude Code + Cursor Integration Design

**Date:** 2026-07-23  
**Status:** Approved in conversation; awaiting implementation  
**Scope:** Developer tooling for HORUS Sentinel — not application runtime LLM

## Goal

Enable Claude Code as a coding assistant alongside Cursor for generating and editing code in this repository: Cursor extension (panel) + standalone CLI (terminal) + a committed project `CLAUDE.md`.

## Non-goals

- Do **not** integrate Anthropic/Claude API into the HORUS brain (`horus_brain/`) or replace Ollama/HF transports.
- Do **not** change agents, API routes, or report-generation behavior.
- Do **not** require Claude for CI or production deploys.

## Prerequisites

- Windows 10+ (this workspace).
- Cursor IDE (VS Code fork).
- Paid Claude plan that includes Claude Code (Pro, Max, Team, Enterprise) **or** Anthropic API billing. Free Claude.ai does not include Claude Code.
- Network access for install and authentication.
- Git for Windows recommended so the CLI can use Bash; PowerShell works without it.

## Architecture

```
┌─────────────────────────────────────────────┐
│ Cursor IDE                                  │
│  ┌─────────────────┐  ┌──────────────────┐  │
│  │ Claude Code     │  │ Integrated       │  │
│  │ extension       │  │ terminal         │  │
│  │ (chat panel,    │  │ → `claude` CLI   │  │
│  │  diffs, @file)  │  │                  │  │
│  └────────┬────────┘  └────────┬─────────┘  │
│           │                    │            │
│           └──────────┬─────────┘            │
│                      ▼                      │
│         Anthropic auth (shared account)     │
│                      │                      │
│                      ▼                      │
│         CLAUDE.md (repo root)               │
│         + code under horus-sentinel/        │
└─────────────────────────────────────────────┘
```

Both surfaces read the same project guidance from `CLAUDE.md` at the git root.

## Components

### 1. Claude Code CLI (machine-local)

- **Install method:** Native Windows installer (preferred over WinGet for auto-update):
  ```powershell
  irm https://claude.ai/install.ps1 | iex
  ```
- **Verify:** `claude --version` after reopening the terminal (PATH refresh).
- **Auth:** First `claude` run opens browser login; credentials shared with the extension.
- **Working directory:** Prefer `horus-sentinel/horus-sentinel/` (Python package root) when running tasks that need `pytest` / `uvicorn`, or repo root when editing docs/pitch. `CLAUDE.md` must state this clearly.

### 2. Claude Code Cursor extension

- **Extension ID:** `anthropic.claude-code`
- **Install:** Cursor Extensions UI (`Ctrl+Shift+X`) → search “Claude Code” → Install; or Anthropic “Install for Cursor” deep link from [IDE integrations docs](https://code.claude.com/docs/en/ide-integrations).
- **Note:** Extension install is a user UI action; the implementer documents steps and cannot silently install marketplace extensions into the user’s Cursor profile from this agent session alone (unless a documented CLI/`cursor` flag is available — treat UI install as the primary path).
- **Use:** Spark (✦) panel / status bar; sign in with the same Anthropic account as the CLI.
- **Fallback:** If the extension breaks after a Cursor update → Developer: Reload Window, or use CLI in the integrated terminal.

### 3. Project `CLAUDE.md` (committed)

**Path:** `CLAUDE.md` at git root  
(`c:\Users\DPQUSD250122\Desktop\horus_sentinel\horus-sentinel\CLAUDE.md`)

**Content requirements (keep tight — one to two screens):**

| Section | Content |
|---------|---------|
| Product | HORUS Sentinel: passive multi-agent OSINT / threat-intel platform; human-validated reports |
| Repo layout | Git root vs nested `horus-sentinel/` application package |
| Commands | From `horus-sentinel/`: `pytest`, `ruff check . && ruff format --check .`, `uvicorn api.main:app --reload` |
| Conventions | Match existing Python style; prefer existing patterns in `agents/`, `api/`, `horus_brain/` |
| Safety | Passive-only / responsible use; never enable unauthorized active recon; do not commit secrets (`.env`, keys) |
| Frozen / careful | Treat `horus-geointel/` as frozen if present; do not invent live infra attacks |

Optional later: `.claude/settings.json` permission allow/deny — **out of scope for v1** unless needed after first sessions.

## File map

| Path | Action | Responsibility |
|------|--------|----------------|
| `CLAUDE.md` | Create | Project guidance for Claude Code (and any agent that reads it) |
| `docs/superpowers/specs/2026-07-23-claude-code-cursor-design.md` | Create | This design |
| App Python packages | No change | Runtime brain stays Ollama/HF/offline |

## Error handling / support notes

- `claude` not found after install → close/reopen terminals; confirm installer PATH; fallback WinGet: `winget install Anthropic.ClaudeCode`.
- Auth failures → verify paid plan / org allowlist / region support.
- Extension missing in marketplace → Open VSX / VSIX per Anthropic docs, or CLI-only.

## Testing / acceptance

1. `claude --version` prints a version in PowerShell (new session).
2. `claude` starts and accepts login (or is already authenticated).
3. Claude Code extension appears in Cursor and opens a chat panel after sign-in.
4. From a session with the repo open, Claude can answer “what is this project?” using `CLAUDE.md` accurately (nested package path + test commands).
5. No application tests required (no runtime code changes). Running `pytest` in `horus-sentinel/` still passes as a smoke check that we did not touch app code.

## Success criteria

Developer can generate/edit code in this repo via Cursor’s Claude Code panel **and** via `claude` in the integrated terminal, with shared project context from `CLAUDE.md`, without changing HORUS Sentinel’s reasoning stack.
