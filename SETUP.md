# HORUS Sentinel — Repository Setup Guide

Follow these steps once, as a team, to get the GitHub repo live and everyone building.

---

## 1. Create the repo on GitHub

1. Go to https://github.com/new
2. **Owner:** `MahmoudAlyosify` (or a team org if you make one)
3. **Repository name:** `horus-sentinel`
4. **Description:** `Autonomous multi-agent OSINT & threat-intelligence platform — ITC-Egypt 2026 Track 3`
5. **Visibility:** Public (recommended — judges & portfolio) *or* Private until submission, then flip to Public
6. **Do NOT** check "Add a README / .gitignore / license" — this scaffold already includes them
7. Click **Create repository**

---

## 2. Push this scaffold

Unzip the provided `horus-sentinel/` folder, then from inside it:

```bash
cd horus-sentinel

git init
git branch -M main
git add .
git commit -m "chore: initial project scaffold (Phase 0 foundation)"

# Replace with YOUR repo URL from step 1
git remote add origin https://github.com/MahmoudAlyosify/horus-sentinel.git
git push -u origin main
```

---

## 3. Add your two teammates as collaborators

Repo → **Settings** → **Collaborators** → **Add people** → add Mirna and Sondos by GitHub username.
(Or, if you created an org, add them to the team.)

---

## 4. Set up branch protection (waterfall discipline)

Repo → **Settings** → **Branches** → **Add branch ruleset** for `main`:
- ✅ Require a pull request before merging
- ✅ Require status checks to pass (select the **CI** check after the first push)
- ✅ Require conversation resolution before merging

This enforces: no one pushes broken code straight to `main`. Since you work waterfall/together, one of you drives the branch, the other two review the PR.

---

## 5. Create the `develop` branch

```bash
git checkout -b develop
git push -u origin develop
```

Workflow: feature branches → `develop` → (at the end of each phase) → `main` + a tag.

---

## 6. Local dev setup (each team member, once)

```bash
# Python env
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Pre-commit hooks (blocks secrets + auto-formats)
pre-commit install

# Copy env template and fill in
cp .env.example .env

# Bring up the infrastructure
docker compose -f deploy/docker-compose.yml up -d

# Verify the API runs
uvicorn api.main:app --reload
#   → open http://localhost:8000/docs and http://localhost:8000/health

# Run the tests
pytest
```

---

## 7. Load the fine-tuned model into Ollama (once)

After `docker compose up`, the Ollama container is running but empty. Load your model:

```bash
# Option A — pull directly from HuggingFace (if the GGUF is published there)
docker exec -it deploy-ollama-1 ollama pull hf.co/mahmoudalyosify/Horus-OSINT

# Option B — from your existing GGUF file + Modelfile (as in the winning project)
#   copy horus-llama3-osint.gguf into the container, then:
docker exec -it deploy-ollama-1 sh -c 'echo "FROM ./horus-llama3-osint.gguf" > Modelfile && ollama create horus-osint -f Modelfile'

# Verify
docker exec -it deploy-ollama-1 ollama list
```

---

## 8. Bring in the winning project (frozen)

Copy your existing Horus-OSINT project files into `horus-geointel/` **unchanged**:

```bash
# from the repo root
cp -r /path/to/your/winning-project/* horus-geointel/
git add horus-geointel/
git commit -m "chore: import award-winning Horus-OSINT project (frozen baseline)"
```

> **Rule:** after this commit, treat everything under `horus-geointel/` as read-only. Build around it.

---

## 9. First tag

Once the scaffold is pushed and the winning project is imported:

```bash
git tag -a v0.1-foundation -m "Phase 0: foundation + frozen winning baseline"
git push origin v0.1-foundation
```

---

## You're ready

Next: **Phase 1 — the Scope & Authorization Engine.** Come back to the assistant and say *"ready for Phase 1"* and we'll write `core/authorization.py` together, on top of the `schemas/roe.py` already in this scaffold.

---

## Quick reference — what's already in this scaffold

| File | Purpose |
|---|---|
| `README.md` | The repo's face (judges see this first) |
| `RESPONSIBLE_USE.md` | Defensive/passive positioning (matters for military judges) |
| `LICENSE` | MIT |
| `.gitignore` | Blocks secrets, models, DB data, node_modules |
| `.env.example` | All config placeholders (copy to `.env`) |
| `requirements.txt` / `requirements-dev.txt` | Pinned dependencies |
| `pyproject.toml` | ruff + mypy + pytest + bandit config |
| `.pre-commit-config.yaml` | Auto-format + secret detection on commit |
| `deploy/docker-compose.yml` | Postgres, Neo4j, Redis, ChromaDB, MinIO, Ollama |
| `.github/workflows/ci.yml` | Lint → type-check → security scan → test |
| `.github/pull_request_template.md` | Enforces the DoD checklist |
| `api/main.py` | Runnable FastAPI skeleton (`/health`) |
| `core/config.py` | Settings from `.env` |
| `schemas/roe.py` | The Rules-of-Engagement model (Phase 1 seed) |
| `tests/` | 5 passing tests (verified) |
| Full package tree | All 12 Python packages + UI folders, ready to fill |
