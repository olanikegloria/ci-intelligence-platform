# Sales playbook — CI Intelligence Platform

---

## ICP (ideal customer profile)

| Dimension | Fit |
|-----------|-----|
| **Company** | 15–200 engineers; GitHub Actions (or Actions-like) as primary CI |
| **Buyer** | Eng Manager, Platform/DevEx lead, or Staff+ engineer owning “CI reliability” |
| **Champion** | IC who already files flake tickets and lives in Actions logs |
| **Trigger** | Release week pain, flake wars in PR review, CI minutes budget pressure |
| **Anti-ICP** | Solo hobby repos; orgs already deep in Datadog CI Visibility + dedicated SRE tooling with no appetite for a focused layer |

**One sentence:** Teams that ship multiple times a week and still lose hours asking “why is this red / is it flaky?”

---

## Pain (what they feel)

1. **Status without causality** — GitHub shows fail; nobody agrees on root cause in the first 15 minutes.  
2. **Recurrence blindness** — Same timeout/assertion returns for weeks without a stable fingerprint.  
3. **Flake vs real break** — Retries and same-SHA pass/fail contradictions are tribal knowledge.  
4. **AI theater risk** — Generic LLM summaries of logs that invent causes destroy trust.

Our wedge: **deterministic fingerprinting and clustering first; AI only narrates cited evidence.**

---

## Demo script (12–15 minutes)

### 0. Setup (30s)

- Open landing `/` → click **Open app** → `/app`  
- Note API uses Bearer auth; local eval token: `demo`

### 1. Problem frame (2 min)

> “Your CI UI answers red/green. We answer: what failed, have we seen it, and is it flaky — with evidence you can verify.”

Show pricing table on landing; point Free → Team as the natural path.

### 2. Ingest + surface (3 min)

```bash
curl -X POST http://localhost:8001/ingest/sample
curl -H "Authorization: Bearer demo" http://localhost:8001/failures
curl -H "Authorization: Bearer demo" http://localhost:8001/flaky-tests
```

Or use dashboard **Reload sample fixtures** and walk failure clusters + flaky table.

### 3. Explain (4 min)

Pick a failed run (e.g. `run-1002`):

```bash
curl -X POST -H "Authorization: Bearer demo" \
  http://localhost:8001/explain/run-1002
```

Narrate: deterministic summary → related fingerprints → evidence → stub AI text that cites those fields (not free-form guesswork).

### 4. Commercial motion (3 min)

```bash
# Signup → token
curl -X POST http://localhost:8001/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"buyer@acme.dev","password":"demo-pass","org_name":"Acme Eng"}'

# Checkout stub (Team)
curl -X POST http://localhost:8001/billing/checkout-session \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"plan":"team"}'
```

Show fake Stripe URL + mention `STRIPE_SECRET_KEY` for production. Optionally burn Free quota with repeated explains until **402**.

### 5. Close (1 min)

> “Team at $49/mo covers a squad and five repos. Same analysis loop you just saw — with seats and quota that match how you actually triage.”

---

## Objection handling

| Objection | Response |
|-----------|----------|
| “We already have Actions / Datadog.” | Complementary: we optimize for **failure recurrence + flake scoring + cited explain**, not full observability. Start Free on one repo. |
| “AI will hallucinate.” | Deterministic fingerprints are source of truth; AI is labeled stub/narration over evidence. No explain without citations in the payload. |
| “$49 is steep for a dashboard.” | You’re buying **triage time and merge confidence**, not charts. One avoided flake war per month pays for Team. |
| “We need GitLab / Jenkins.” | Honest scope: Actions-shaped model first. Data model is CI-agnostic; adapters are roadmap, not vapor in the pitch. |
| “Security / SSO?” | Auth-lite + org tokens today; Business plan narrative includes SSO-ready. Offer self-host conversation for regulated buyers. |
| “Will this lock us in?” | Export/API-first; store is JSON today for transparency. Checkout is Stripe-standard. |

---

## Qualification questions

1. How many repos block merges on CI daily?  
2. Who owns flake quarantine today?  
3. Do you already pay for CI visibility — what’s still missing?  
4. Seat count for the squad that would use this weekly?
