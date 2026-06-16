# ARGUS — Week 1: Foundation + Authorization Engine

## Run locally (no Docker)

```bash
pip install -r requirements-dev.txt
cp .env.example .env   # uses SQLite-friendly defaults are NOT set here —
                        # for local Postgres-free testing, just run pytest.
uvicorn api.main:app --reload
```

By default `core/config.py` points at a local Postgres at
`postgresql+asyncpg://argus:argus@localhost:5432/argus`. Easiest path:

```bash
docker compose up        # starts Postgres + Redis + the API on :8000
```

Then open http://localhost:8000/docs.

## Try the gate manually

Two pre-signed RoE records are in `examples/` (signed with the dev key in
`.env.example` — regenerate with `scripts/sign_roe.py` if you change
`ARGUS_ROE_SIGNING_KEY`):

- `examples/roe_passive_only.json` — `example.com`, passive only
- `examples/roe_with_active_scanning.json` — `example.com`, active scanning
  authorized, restricted to `nmap`

```bash
# in scope -> 201 authorized
curl -X POST localhost:8000/jobs -H "Content-Type: application/json" -d '{
  "apex_domain": "example.com",
  "roe": '"$(cat examples/roe_passive_only.json)"'
}'

# out of scope -> 403
curl -X POST localhost:8000/jobs -H "Content-Type: application/json" -d '{
  "apex_domain": "not-example.com",
  "roe": '"$(cat examples/roe_passive_only.json)"'
}'
```

## Tests

```bash
python -m pytest -q     # 28 tests, SQLite-backed, no Docker needed
python -m ruff check .
```

Covers: signature tamper-detection, expired RoE, domain/CIDR scope
matching (including subdomain suffix matching and exclusions),
passive-vs-active gating, active-tool allow-lists, and that the same gate
enforced at the `/jobs` API is *also* enforced inside `ReconTool.__call__`
(so an agent can't bypass it by calling a tool directly).

## What's NOT done yet (by design, per the 8-week plan)

- No actual collection tools yet (`tools/whois_tool.py` etc. — week 2)
- No LangGraph orchestrator (`workflows/recon_graph.py` — week 5); jobs sit
  at `status=authorized` and nothing consumes them yet
- Redis-backed cache/rate-limit/queue — current `core/cache.py` and
  `core/rate_limit.py` are in-memory per-process placeholders behind the
  final interface, swapped for Redis when the queue lands in week 3
- Alembic migrations — using `create_all` on startup for now
