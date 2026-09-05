# CI Intelligence Platform

**Status:** SaaS foundation (auth, metering, commercial docs) on a runnable analysis MVP  
**Folder:** `01-ci-intelligence-platform`

Explain *why* CI failed and whether it will happen again — deterministic fingerprinting and clustering first, AI explanation second (stub that cites evidence).

---

## Path to selling

| Stage | What ships here | Next production step |
|-------|-----------------|----------------------|
| **1. Prove value** | Landing `/`, dashboard `/app`, sample ingest, clusters / flakes / explain | Connect real GitHub Actions webhooks |
| **2. Capture account** | `POST /auth/signup` + `/auth/login` → API token; orgs in `data/accounts.json` | Managed Postgres + password reset |
| **3. Meter Free** | 50 explains/mo; **HTTP 402** on quota | Soft alerts + in-app upgrade CTA |
| **4. Take payment** | `POST /billing/checkout-session` stub + fake Stripe URL | Set `STRIPE_SECRET_KEY`, real Checkout + webhooks → plan upgrade |
| **5. Close Team/Business** | Pricing/Sales docs; seat+repo narrative | Enforce seats/repos; SSO for Business |

Commercial docs:

- [docs/PRICING.md](./docs/PRICING.md) — Free / Team ($49) / Business ($199)
- [docs/SALES.md](./docs/SALES.md) — ICP, demo script, objections

Legal stubs: `/legal/terms`, `/legal/privacy`

---

## What works

- Marketing landing at `/`; product dashboard at `/app` (alias `/dashboard`)
- Ingest sample GitHub Actions–like workflow runs
- Bearer-protected analysis APIs (`demo` token for local eval)
- Org signup/login with API tokens; usage metering; checkout stub
- Failure clusters, flaky-test scoring, evidence-cited `POST /explain/{run_id}`

## Stack

| Layer | Choice |
|-------|--------|
| API + UI | Python FastAPI + Jinja |
| Store | JSON under `data/` (`store.json`, `accounts.json`) |
| Auth | PBKDF2 password hashes + opaque API tokens |
| Billing | Stripe Checkout stub (`STRIPE_SECRET_KEY` for later) |
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
# optional later: export STRIPE_SECRET_KEY=sk_test_...
uvicorn app.main:app --reload --port 8001
```

Open http://localhost:8001/ (landing) and http://localhost:8001/app (dashboard).

### Commercial demo flow

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

# Signup → Free org token
curl -X POST http://localhost:8001/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"buyer@acme.dev","password":"demo-pass","org_name":"Acme Eng"}'
# → { "token": "...", "plan": "free", ... }

# Checkout stub (Team)
curl -X POST http://localhost:8001/billing/checkout-session \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"plan":"team"}'
# → fake https://checkout.stripe.com/c/pay/cs_test_fake_...
```

Free orgs that exceed **50 explains/month** receive **402** with upgrade hints.

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
| GET | `/` | — | Marketing landing |
| GET | `/app`, `/dashboard` | — | Analysis dashboard |
| GET | `/legal/terms`, `/legal/privacy` | — | Legal stubs |
| GET | `/health` | — | Liveness |
| POST | `/ingest/sample` | — | Load fixture runs |
| POST | `/auth/signup` | — | Create org + user + API token |
| POST | `/auth/login` | — | Return API token |
| GET | `/billing/usage` | Bearer | Plan + explain usage |
| POST | `/billing/checkout-session` | Bearer | Stub Stripe Checkout URL |
| GET | `/runs`, `/runs/{id}` | Bearer | List / get runs |
| GET | `/failures` | Bearer | Clustered failure signatures |
| GET | `/flaky-tests` | Bearer | Flaky score heuristics |
| POST | `/explain/{run_id}` | Bearer | Explain (meters usage; 402 on Free limit) |

Local eval: `Authorization: Bearer demo`

## Env

| Variable | Purpose |
|----------|---------|
| `DATA_DIR` | JSON persistence (default `./data`) |
| `FIXTURES_DIR` | Sample runs path |
| `STRIPE_SECRET_KEY` | Required later for live Checkout (documented on stub response) |
| `STRIPE_WEBHOOK_SECRET` | Optional; plan upgrades on `invoice.paid` |
| `STRIPE_PRICE_TEAM` / `STRIPE_PRICE_BUSINESS` | Optional Stripe Price IDs |

## Layout

```text
backend/app/        FastAPI, auth, accounts, analysis, store
backend/templates/  landing, dashboard, legal HTML
docs/               PRICING.md, SALES.md
fixtures/           sample_runs.json
tests/              fingerprint + auth/metering pytest
```

## Docs

- [PROPOSAL.md](./PROPOSAL.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [INTERVIEW.md](./INTERVIEW.md)
- [docs/PRICING.md](./docs/PRICING.md)
- [docs/SALES.md](./docs/SALES.md)
