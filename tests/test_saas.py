"""Tests for auth, metering, and commercial stubs."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.accounts import accounts
from app.main import app
from app.store import store


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv(
        "FIXTURES_DIR",
        str(Path(__file__).resolve().parents[1] / "fixtures"),
    )
    # Reset singletons for isolated temp data dir
    store.runs.clear()
    accounts.orgs.clear()
    accounts.users.clear()
    accounts.tokens.clear()
    accounts.load()
    store.load()
    if not store.runs:
        from app.main import _ingest_fixtures

        _ingest_fixtures()

    with TestClient(app) as c:
        yield c


def test_landing_and_app_routes(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"CI Intelligence" in r.content

    r = client.get("/app")
    assert r.status_code == 200
    assert b"Workflow runs" in r.content

    assert client.get("/dashboard").status_code == 200
    assert client.get("/legal/terms").status_code == 200
    assert client.get("/legal/privacy").status_code == 200


def test_protected_routes_require_auth(client):
    assert client.get("/runs").status_code == 401
    assert client.get("/failures").status_code == 401
    assert client.get("/flaky-tests").status_code == 401
    assert client.post("/explain/run-1002").status_code == 401


def test_demo_token_and_ingest(client):
    headers = {"Authorization": "Bearer demo"}
    ing = client.post("/ingest/sample")
    assert ing.status_code == 200
    assert ing.json()["ingested"] > 0

    runs = client.get("/runs", headers=headers)
    assert runs.status_code == 200
    assert len(runs.json()) > 0

    expl = client.post("/explain/run-1002", headers=headers)
    assert expl.status_code == 200
    body = expl.json()
    assert body["run_id"] == "run-1002"
    assert body["deterministic_summary"]


def test_signup_login_checkout_and_free_quota(client):
    signup = client.post(
        "/auth/signup",
        json={
            "email": "Buyer@Acme.Dev",
            "password": "secret12",
            "org_name": "Acme Eng",
        },
    )
    assert signup.status_code == 200
    token = signup.json()["token"]
    assert signup.json()["plan"] == "free"
    headers = {"Authorization": f"Bearer {token}"}

    login = client.post(
        "/auth/login",
        json={"email": "buyer@acme.dev", "password": "secret12"},
    )
    assert login.status_code == 200
    assert login.json()["token"]

    client.post("/ingest/sample")

    org_id = signup.json()["org_id"]
    month = accounts.usage_snapshot(org_id)["month"]
    accounts.orgs[org_id]["usage"] = {month: {"explains": 50}}
    accounts._persist()

    blocked = client.post("/explain/run-1002", headers=headers)
    assert blocked.status_code == 402
    detail = blocked.json()["detail"]
    assert detail["error"] == "quota_exceeded"

    checkout = client.post(
        "/billing/checkout-session",
        headers=headers,
        json={"plan": "team"},
    )
    assert checkout.status_code == 200
    payload = checkout.json()
    assert payload["url"].startswith("https://checkout.stripe.com/")
    assert "STRIPE_SECRET_KEY" in payload["env"]
