# Pricing — CI Intelligence Platform

**Positioning:** Pay for seats and repos that need failure intelligence — not for another CI status board.

---

## Plans at a glance

| | **Free** | **Team** | **Business** |
|---|----------|----------|--------------|
| **Price** | $0 | **$49 / month** | **$199 / month** |
| **Seats** | 1 | Up to 10 | Up to 50 |
| **Repos** | 1 | Up to 5 | Up to 25 |
| **Explains / month** | 50 | 2,000 | Unlimited\* |
| **Failure clusters** | Yes | Yes | Yes |
| **Flaky-test scoring** | Yes | Yes | Yes + export |
| **API tokens** | 1 | Per seat | SSO-ready (roadmap) |
| **Support** | Community docs | Email (48h) | Priority + shared Slack |

\*Fair-use rate limits still apply on Business to protect the service.

---

## Seat + repo narrative (how buyers should think about it)

### Free — prove the loop on one repo

One engineer, one repository, fifty evidence-cited explains per month. Enough to ingest sample (or real) runs, see clusters and flakes, and decide whether the product saves triage time. When the Free explain quota is hit, the API returns **HTTP 402** with a clear upgrade path — not a silent failure.

### Team ($49/mo) — the buying unit for most startups

Ten seats cover a squad that shares CI pain: backend + mobile + a platform owner. Five repos is typically “product monorepo + 2–4 services.” Two thousand explains/month covers daily failure triage without nickel-and-diming every click. This is the default close for Series A–B engineering orgs that already burn hours on red builds.

### Business ($199/mo) — platform / multi-team reliability

Fifty seats and twenty-five repos fit a platform team serving multiple product groups. Unlimited explains (fair use) removes quota anxiety for on-call and release weeks. Export and priority support matter when flaky-test data feeds engineering OKRs or incident reviews.

---

## What we meter today (MVP)

| Meter | Free limit | Notes |
|-------|------------|-------|
| `POST /explain/{run_id}` | **50 / calendar month / org** | Enforced in-app; 402 when exceeded |
| Seats / repos | Soft limits in docs | Hard enforcement ships with billing webhooks |

Auth and org identity are required for protected analysis APIs. Local demos may use the Bearer token `demo`.

---

## Upgrade path

1. Sign up → Free org + API token  
2. Hit quota or need more seats/repos → `POST /billing/checkout-session`  
3. Stripe Checkout (production: set `STRIPE_SECRET_KEY`) → Team or Business  

Checkout in this codebase is a **stub** that returns a fake Stripe URL so the commercial flow is demoable before payment credentials are wired.
