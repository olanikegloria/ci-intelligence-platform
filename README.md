# CI Intelligence Platform

**Status:** Runnable MVP scaffold  
**Folder:** `01-ci-intelligence-platform`

Explain *why* CI failed and whether it will happen again — deterministic fingerprinting and clustering first, AI explanation second (stub that cites evidence).

---

## What works in this MVP

- Ingest sample GitHub Actions–like workflow runs (success, failures, flakes)
- List runs, cluster failure signatures (count / first seen / last seen)
- Flaky-test scoring heuristics (same-SHA pass+fail, retry recovery)
- `POST /explain/{run_id}` — deterministic summary + stub AI narrative with citations
- Dashboard UI at `/` (Jinja template served by FastAPI)

## Stack

| Layer | Choice |
|-------|--------|
| API + UI | Python FastAPI + Jinja |
| Store | In-memory + JSON file (`data/store.json`) |
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

Open http://localhost:8001/

```bash
# API checks
curl -X POST http://localhost:8001/ingest/sample
curl http://localhost:8001/runs | head
curl http://localhost:8001/failures
curl http://localhost:8001/flaky-tests
curl -X POST http://localhost:8001/explain/run-1002
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

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard |
| POST | `/ingest/sample` | Load fixture runs |
| GET | `/runs` | List workflow runs |
| GET | `/failures` | Clustered failure signatures |
| GET | `/flaky-tests` | Flaky score heuristics |
| POST | `/explain/{run_id}` | Deterministic + stub AI explanation |

## Layout

```text
backend/app/     FastAPI, models, fingerprinting, analysis, store
backend/templates/  Dashboard HTML
fixtures/        sample_runs.json
tests/           fingerprint + clustering pytest
frontend/        UI is served by FastAPI at / (see note below)
```

The `frontend/` folder is reserved for a future Next.js app; the MVP ships a working dashboard from FastAPI for a single-process demo.

## Docs

- [PROPOSAL.md](./PROPOSAL.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [INTERVIEW.md](./INTERVIEW.md)
