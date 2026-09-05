"""CI Intelligence Platform — FastAPI API + landing + dashboard UI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .accounts import accounts
from .analysis import cluster_failures, explain_run, score_flaky_tests
from .auth import AuthContext
from .models import ExplainResponse, FailureSignature, FlakyTest, WorkflowRun
from .store import store

ROOT = Path(__file__).resolve().parents[1]  # backend/
PROJECT_ROOT = ROOT.parent
FIXTURES_DIR = Path(os.environ.get("FIXTURES_DIR", PROJECT_ROOT / "fixtures"))
TEMPLATES_DIR = ROOT / "templates"

app = FastAPI(
    title="CI Intelligence Platform",
    description="Failure clustering, flaky-test scoring, and evidence-cited explanations",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class SignupRequest(BaseModel):
    email: str
    password: str
    org_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


@app.on_event("startup")
def startup() -> None:
    store.load()
    accounts.load()
    if not store.runs:
        _ingest_fixtures()


def _ingest_fixtures() -> dict:
    path = FIXTURES_DIR / "sample_runs.json"
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    payload = json.loads(path.read_text())
    count = 0
    for item in payload.get("runs", []):
        run = WorkflowRun.model_validate(item)
        store.upsert_run(run)
        count += 1
    return {"ingested": count, "source": str(path)}


@app.get("/", response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/app", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    runs = store.list_runs()
    clusters = cluster_failures(runs)
    flaky = score_flaky_tests(runs)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "runs": runs,
            "clusters": clusters,
            "flaky": flaky,
        },
    )


@app.get("/legal/terms", response_class=HTMLResponse)
def legal_terms(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("legal_terms.html", {"request": request})


@app.get("/legal/privacy", response_class=HTMLResponse)
def legal_privacy(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("legal_privacy.html", {"request": request})


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "runs": len(store.runs)}


@app.post("/ingest/sample")
def ingest_sample() -> dict:
    store.clear()
    return _ingest_fixtures()


@app.post("/auth/signup")
def auth_signup(body: SignupRequest) -> dict[str, Any]:
    try:
        return accounts.signup(body.email, body.password, body.org_name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/auth/login")
def auth_login(body: LoginRequest) -> dict[str, Any]:
    try:
        return accounts.login(body.email, body.password)
    except ValueError as exc:
        raise HTTPException(401, str(exc)) from exc


@app.get("/runs", response_model=list[WorkflowRun])
def list_runs(_auth: AuthContext) -> list[WorkflowRun]:
    return store.list_runs()


@app.get("/runs/{run_id}", response_model=WorkflowRun)
def get_run(run_id: str, _auth: AuthContext) -> WorkflowRun:
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(404, f"Run {run_id} not found")
    return run


@app.get("/failures", response_model=list[FailureSignature])
def list_failures(_auth: AuthContext) -> list[FailureSignature]:
    return cluster_failures(store.list_runs())


@app.get("/flaky-tests", response_model=list[FlakyTest])
def list_flaky(_auth: AuthContext) -> list[FlakyTest]:
    return score_flaky_tests(store.list_runs())


@app.post("/explain/{run_id}", response_model=ExplainResponse)
def explain(run_id: str, _auth: AuthContext) -> ExplainResponse:
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(404, f"Run {run_id} not found")
    clusters = cluster_failures(store.list_runs())
    payload = explain_run(run, clusters)
    return ExplainResponse(**payload)
