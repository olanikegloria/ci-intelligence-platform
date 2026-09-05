# Architecture — CI Intelligence Platform

**Status:** Planning. Subject to change after proposal review.

---

## System overview

```text
GitHub Actions
     │ webhooks + REST API
     ▼
Ingestion API (FastAPI)
     │
     ├── Normalizer (runs / jobs / steps / tests / logs)
     ├── Object store / DB for log blobs (size-capped)
     └── Queue (Redis)
              │
              ▼
         Analysis Workers
         - failure clustering
         - change correlation (PR/commit)
         - flaky-test scoring
         - metrics / durations
              │
              ▼
         PostgreSQL (facts + derived signals)
              │
     ┌────────┴────────┐
     ▼                 ▼
  Next.js UI      AI Explainer
  (dashboards)    (log summary, RCA narrative,
                   Q&A over stored facts)
```

---

## Core components

| Component | Responsibility |
|-----------|----------------|
| `backend/` | FastAPI: webhooks, auth, query APIs |
| `backend/` workers | Async analysis jobs |
| `frontend/` | Failure views, flaky tests, incident summaries |
| `infrastructure/` | Docker Compose, GH Actions CI for this product |
| `tests/` | Unit + API + analysis fixture tests |

---

## Data model (MVP sketch)

- `repositories`, `installations` (GitHub App or OAuth later; PAT for early MVP)
- `workflow_runs`, `jobs`, `steps`
- `test_results` (from parsed JUnit / annotations where available)
- `failure_signatures` (normalized error fingerprint)
- `failure_clusters` (grouped signatures + first/last seen)
- `flaky_tests` (pass/fail on same SHA, retry recovery)
- `ai_explanations` (cached, tied to run/cluster ids)

---

## Deterministic vs AI

| Deterministic | AI |
|---------------|-----|
| Ingest, parse, store | Explain a failed run in plain language |
| Fingerprint errors | Summarise long logs (bounded context) |
| Correlate failing run with PR/commit diffs metadata | Suggest next debugging steps |
| Flake score from history | Group narrative across similar failures |
| Duration / bottleneck stats | Answer “has this happened before?” using retrieved facts |

AI must cite stored run IDs, signatures, and test names. No free-form invention of causes without evidence flags.

---

## Security

- Verify GitHub webhook signatures
- Encrypt tokens at rest
- Redact secrets in logs before storage (heuristic patterns)
- Rate-limit public APIs
- Least-privilege GitHub permissions

---

## Scalability notes

| Scale | Approach |
|-------|----------|
| Solo / demo | Single Compose stack; sample fixtures |
| Small team | Per-repo ingest; log truncation; retention TTL |
| Large | Partition by repo; sample logs; async backpressure; separate analytics DB |

---

## Open architecture questions (for review)

1. GitHub App vs PAT for MVP?
2. How much raw log text to retain vs fingerprints only?
3. First test report format to support (JUnit XML)?
