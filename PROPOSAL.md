# PROJECT PROPOSAL — 01 CI Intelligence Platform

**Status:** Awaiting review. Do not implement until accepted.  
**Working name:** CI Intelligence Platform  
**One-liner:** Explain *why* CI failed and whether it will happen again — with deterministic analysis first, AI explanation second.

---

## PROBLEM

CI dashboards answer “red or green.” They rarely answer:

- Why did this run fail?
- Is this the same failure as last Tuesday?
- Did a specific PR introduce it?
- Is the test flaky or genuinely broken?
- Which step is getting slower over time?

Engineers lose hours re-reading logs, correlating PRs by hand, and arguing about flakes.

---

## TARGET USER

- Software engineers shipping via GitHub Actions
- DevOps / platform engineers owning pipeline reliability
- Engineering managers tracking delivery risk

---

## WHY THEY CARE

Failed or flaky CI blocks merges, burns CI minutes, and erodes trust in the test suite. Faster root-cause understanding and flake visibility directly improve throughput.

---

## EXISTING ALTERNATIVES

| Alternative | What it does well | Gap relative to this project |
|-------------|-------------------|------------------------------|
| GitHub Actions UI | Status, logs, annotations | Weak cross-run causality and flake intelligence |
| Trunk Flaky Tests, BuildPulse | Flake detect / quarantine | Broader “why this failure / recurrence” narrative less central |
| Datadog CI Visibility, Launchable | Observability / test selection | Heavier platform; less portfolio-sized; paid |
| Custom scripts / Notion postmortems | Ad hoc | Not continuous or structured |

We are **not** claiming to invent CI intelligence. We are building a sharp, interviewable implementation with a clear angle.

---

## OUR DIFFERENTIATOR

1. **Failure causality + recurrence** as the primary product question — not “another dashboard.”
2. **Deterministic fingerprinting and clustering** as the source of truth; AI only narrates evidence.
3. **Flaky-test scoring** as an advanced layer on the same data model (retries, same-SHA contradiction, env hints).
4. Honest scope: GitHub Actions first; depth over multi-CI breadth.

---

## MVP

- Connect a GitHub repo (PAT or GitHub App — decide at build; PAT acceptable for demo)
- Ingest workflow runs, jobs, steps, conclusions, durations, branch, commit, PR, actor
- Store and display failure history
- Error fingerprinting + cluster “first seen / last seen / count”
- Correlate clusters with introducing commit/PR when possible
- Bounded log summary via AI with citations to run/step IDs
- Basic flaky signal: same test/name pass+fail on same commit SHA and/or pass after retry

**Non-goals for MVP:** multi-CI vendors, auto-quarantine bots, full ML test selection, enterprise SSO.

---

## V2

- Richer test report ingestion (JUnit XML)
- Flakiness score (HIGH/MED/LOW) with supporting stats UI
- “Diff successful vs failed run” explanation
- Slack/GitHub Check annotations
- Retention policies and log sampling controls

---

## V3

- Cross-repo org views
- Predictive “likely flake vs likely real” assist
- Incident summary export for postmortems
- Policy hooks (warn on rising flake rate)

---

## TECH STACK

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | Next.js, TS, React, Tailwind | Portfolio consistency, strong UI for investigations |
| Backend | Python / FastAPI | Log/data pipelines, analysis code, AI glue |
| DB | PostgreSQL | Relational facts + JSON for flexible payloads |
| Queue | Redis + worker | Webhook spikes, log processing |
| Infra | Docker Compose, GitHub Actions | Matches domain; free local demo |
| AI | Ollama + provider interface | Free/local; swappable |

---

## ARCHITECTURE

See [ARCHITECTURE.md](./ARCHITECTURE.md).

Summary: webhook/API ingest → normalize → queue → analysis workers → Postgres → UI + AI explainer over stored facts.

---

## AI COMPONENT

**Where AI helps**

- Summarise truncated logs
- Explain likely cause *given* fingerprints, step names, and recent changes metadata
- Group narrative for similar failures
- Answer questions about history using retrieved runs/clusters

**Where AI must not be used**

- Replacing fingerprinting
- Inventing root causes without evidence
- “AI-powered CI” marketing without a deterministic core

**Eval (when built)**

- Explanation cites real run/step IDs
- Hallucinated file/test names rate
- Latency and token/cost proxies for local models

---

## SECURITY

- Webhook signature verification
- Encrypted GitHub tokens
- Secret redaction heuristics on logs
- Auth for private repo data
- Rate limits on APIs

---

## SCALABILITY

| Scale | Plan |
|-------|------|
| 10 users | Single Compose; full logs truncated to N KB/step |
| 10k users | Per-repo shards, aggressive retention, sample logs, horizontal workers |
| 1M users | Multi-tenant isolation, streaming ingest, columnar analytics store, tiered storage |

---

## TESTING

- Unit: fingerprint normalization, flake heuristics
- Integration: webhook → DB fixtures
- API tests: run query endpoints
- Golden fixtures of real anonymised logs
- AI eval set for summaries/refusals

---

## DEPLOYMENT

- Docker Compose for local/demo
- CI: lint → test → build images
- Hosted demo later on free-tier friendly VPS or Render/Fly if needed (decide at build)

---

## ESTIMATED COMPLEXITY

**High** — ingest + log handling + analysis quality dominate. Feasible as a strong portfolio MVP if GitHub Actions–only and log retention is capped.

---

## RISKS

| Risk | Mitigation |
|------|------------|
| Log volume / storage cost | Truncate, hash, TTL |
| GitHub API rate limits | Conditional requests, caching, App auth later |
| Flake false positives | Conservative rules; show evidence counts |
| Weak differentiator vs Trunk/etc. | Emphasise causality+recurrence UX and open architecture narrative |
| AI inventing causes | Require citations; confidence/refuse |

---

## ACCEPTANCE

- [ ] Differentiator sharp enough
- [ ] MVP cut approved
- [ ] Stack approved
- [ ] **I accept this** / revise / cut
