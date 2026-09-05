# Frontend

The MVP dashboard is served by the FastAPI backend at `GET /` (`backend/templates/index.html`).

A standalone Next.js app can replace this later without changing the JSON API (`/runs`, `/failures`, `/flaky-tests`, `/explain/{run_id}`).
