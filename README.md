# CI Intelligence Platform

**Status:** Phase 0 — planning only. Do not implement until proposal is accepted.  
**Folder:** `01-ci-intelligence-platform`

---

## Problem

Engineering teams struggle to answer: **why did this pipeline fail, and is it likely to happen again?** Existing dashboards show status; they rarely explain causality, recurrence, or flakiness with enough structure to act.

## Target users

Software engineers, DevOps/platform engineers, engineering managers.

## Solution (intent)

Ingest GitHub Actions data (runs, jobs, steps, tests, logs, PRs, commits). Run deterministic analysis for failure clustering, timelines, and flaky-test scoring. Use AI on top of that data to explain failures, summarise logs, and answer questions about pipeline history — not to replace the analysis engine.

## Tech stack (planned)

- Frontend: Next.js, TypeScript, React, Tailwind
- Backend: Python / FastAPI
- Database: PostgreSQL
- Jobs: Redis + worker
- Infra: Docker, GitHub Actions
- AI: Ollama / open models via a provider interface

## Docs

- [PROPOSAL.md](./PROPOSAL.md) — full proposal for review
- [ARCHITECTURE.md](./ARCHITECTURE.md) — system design
- [INTERVIEW.md](./INTERVIEW.md) — interview stub

## Setup

Not runnable yet. Scaffold only.
