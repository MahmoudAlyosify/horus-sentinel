# HORUS Sentinel — developer & deploy shortcuts.
# Run from the project directory (this folder). `make help` lists everything.
#
# Notes:
#   * Docker targets need only Docker + Compose v2.
#   * Local targets (run/test/lint) assume your virtualenv is ACTIVATED, or override PY=
#     e.g.  make test PY=.venv/bin/python   (Windows venv: PY=.venv/Scripts/python)
#   * WINDOWS: `make` is not built in. Either run these targets from Git Bash, or skip make
#     and use the raw commands in AGENT_HANDOFF.md / RUN.md (docker compose / uvicorn work
#     natively in PowerShell). curl targets below assume a Unix shell (in PowerShell use
#     `curl.exe`, since `curl` is an alias for Invoke-WebRequest there).

PY      ?= python
COMPOSE ?= docker compose -f deploy/docker-compose.yml
BASE_URL ?= http://localhost:8000

.DEFAULT_GOAL := help

# ---- meta -------------------------------------------------------------------
.PHONY: help
help: ## Show this help
	@echo "HORUS Sentinel — make targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | sort \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ---- local (no Docker) ------------------------------------------------------
.PHONY: install
install: ## Create .venv and install dev dependencies
	$(PY) -m venv .venv
	@echo "Virtualenv created. Activate it, then: make deps"

.PHONY: deps
deps: ## Install dev dependencies into the active environment
	$(PY) -m pip install -U pip
	$(PY) -m pip install -r requirements-dev.txt

.PHONY: run
run: ## Run the API + Command Center locally (SQLite, offline-capable) at :8000
	$(PY) -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: worker
worker: ## Run a standalone async worker (consumes the job queue)
	$(PY) -m workflows.worker

# ---- quality ----------------------------------------------------------------
.PHONY: test
test: ## Run the test suite (offline, network mocked)
	$(PY) -m pytest -q

.PHONY: lint
lint: ## Lint with ruff
	$(PY) -m ruff check .

.PHONY: format
format: ## Auto-format with ruff
	$(PY) -m ruff format .

.PHONY: typecheck
typecheck: ## Type-check the typed subset (core/tools/schemas) with mypy
	$(PY) -m mypy

.PHONY: check
check: lint typecheck test ## Run lint + typecheck + tests (CI-equivalent)

# ---- Docker full stack ------------------------------------------------------
.PHONY: up
up: ## Build + start the full stack (api, worker, datastores, ollama)
	$(COMPOSE) up -d --build

.PHONY: down
down: ## Stop the stack (keeps data volumes)
	$(COMPOSE) down

.PHONY: down-hard
down-hard: ## Stop the stack AND wipe all data volumes
	$(COMPOSE) down -v

.PHONY: ps
ps: ## Show stack container status
	$(COMPOSE) ps

.PHONY: logs
logs: ## Follow api + worker logs
	$(COMPOSE) logs -f api worker

.PHONY: scale-workers
scale-workers: ## Scale async workers: make scale-workers N=3
	$(COMPOSE) up -d --scale worker=$(or $(N),2)

# ---- model (Ollama, GPU) ----------------------------------------------------
.PHONY: model-pull
model-pull: ## Load the fine-tuned model into Ollama (one-time, uses the GPU)
	$(COMPOSE) exec ollama ollama pull hf.co/mahmoudalyosify/Horus-OSINT

.PHONY: model-list
model-list: ## List models served by Ollama
	$(COMPOSE) exec ollama ollama list

# ---- smoke / verify ---------------------------------------------------------
.PHONY: health
health: ## Curl the health endpoint
	curl -s $(BASE_URL)/health && echo

.PHONY: demo
demo: ## Run the one-click Guided Demo via the API
	curl -s -X POST $(BASE_URL)/demo && echo

.PHONY: verify
verify: ## Quick end-to-end verification (health + guided demo)
	@echo ">> health:"   && curl -s $(BASE_URL)/health && echo
	@echo ">> demo:"     && curl -s -X POST $(BASE_URL)/demo && echo
	@echo ">> UI:"       && curl -s -o /dev/null -w "  /ui -> HTTP %{http_code}\n" $(BASE_URL)/ui/

# ---- housekeeping -----------------------------------------------------------
.PHONY: clean
clean: ## Remove caches, local SQLite DB, and generated reports
	rm -rf .pytest_cache .ruff_cache .mypy_cache **/__pycache__ __pycache__
	rm -f horus_sentinel.db
	rm -rf data/reports data/chroma
