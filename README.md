# CI Intelligence Platform

**Status:** Production-ready analysis MVP (auth + multi-user orgs)  
**Folder:** `01-ci-intelligence-platform`

Explain *why* CI failed and whether it will happen again — deterministic fingerprinting and clustering first, AI explanation second (stub that cites evidence).

Legal stubs: `/legal/terms`, `/legal/privacy`

---

## What works

- Product landing at `/`; analysis dashboard at `/app` (alias `/dashboard`)
- Ingest sample GitHub Actions–like workflow runs
- Bearer-protected analysis APIs (`demo` token for local eval)
- Org signup/login with API tokens
- Failure clusters, flaky-test scoring, evidence-cited `POST /explain/{run_id}`

## Stack

| Layer | Choice |
|-------|--------|
| API + UI | Python FastAPI + Jinja |
| Store | JSON under `data/` (`store.json`, `accounts.json`) |
| Auth | PBKDF2 password hashes + opaque API tokens |
| Tests | pytest |
| Infra | Docker Compose |

## Quick start (local)

```bash
cd 01-ci-intelligence-platform
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export PYTHONPATH=backend
export FIXTURES_DIR=$PWD/fixtures
export DATA_DIR=$PWD/data
uvicorn app.main:app --reload --port 8001
```

Open http://localhost:8001/ (landing) and http://localhost:8001/app (dashboard).

### Try the APIs

```bash
# Public: reload fixtures (no auth)
curl -X POST http://localhost:8001/ingest/sample

# Local eval token
export TOKEN=demo

curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/runs
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/failures
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/flaky-tests
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/explain/run-1002

# Signup → org API token
curl -X POST http://localhost:8001/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@acme.dev","password":"demo-pass","org_name":"Acme Eng"}'
```

### Tests

```bash
cd 01-ci-intelligence-platform
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend pytest tests/ -q
```

## Docker

```bash
cd 01-ci-intelligence-platform
docker compose up --build
```

UI/API: http://localhost:8001/

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | — | Product landing |
| GET | `/app`, `/dashboard` | — | Analysis dashboard |
| GET | `/legal/terms`, `/legal/privacy` | — | Legal stubs |
| GET | `/health` | — | Liveness |
| POST | `/ingest/sample` | — | Load fixture runs |
| POST | `/auth/signup` | — | Create org + user + API token |
| POST | `/auth/login` | — | Return API token |
| GET | `/runs`, `/runs/{id}` | Bearer | List / get runs |
| GET | `/failures` | Bearer | Clustered failure signatures |
| GET | `/flaky-tests` | Bearer | Flaky score heuristics |
| POST | `/explain/{run_id}` | Bearer | Evidence-cited explanation |

Local eval: `Authorization: Bearer demo`

## Env

| Variable | Purpose |
|----------|---------|
| `DATA_DIR` | JSON persistence (default `./data`) |
| `FIXTURES_DIR` | Sample runs path |

## Layout

```text
backend/app/        FastAPI, auth, accounts, analysis, store
backend/templates/  landing, dashboard, legal HTML
fixtures/           sample_runs.json
tests/              fingerprint + auth pytest
```

## Docs

- [PROPOSAL.md](./PROPOSAL.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [INTERVIEW.md](./INTERVIEW.md)
