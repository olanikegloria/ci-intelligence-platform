"""Org / user / token / usage store (JSON under data/)."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_DATA = Path(__file__).resolve().parents[2] / "data"


def _data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", _DEFAULT_DATA))


def _accounts_path() -> Path:
    return _data_dir() / "accounts.json"

DEMO_TOKEN = "demo"
DEMO_ORG_ID = "org_demo"
DEMO_EMAIL = "demo@localhost"

# Plan limits: explains per calendar month (None = unlimited)
PLAN_EXPLAIN_LIMITS: dict[str, int | None] = {
    "free": 50,
    "team": 2000,
    "business": None,
}

PLAN_SEATS: dict[str, int] = {"free": 1, "team": 10, "business": 50}
PLAN_REPOS: dict[str, int] = {"free": 1, "team": 5, "business": 25}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _month_key(when: datetime | None = None) -> str:
    dt = when or datetime.now(timezone.utc)
    return f"{dt.year:04d}-{dt.month:02d}"


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, _digest = stored.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(hash_password(password, salt), stored)


class AccountsStore:
    def __init__(self) -> None:
        self.orgs: dict[str, dict[str, Any]] = {}
        self.users: dict[str, dict[str, Any]] = {}  # keyed by lowercased email
        self.tokens: dict[str, dict[str, Any]] = {}  # keyed by token string
        _data_dir().mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        path = _accounts_path()
        if not path.exists():
            self._ensure_demo()
            self._persist()
            return
        raw = json.loads(path.read_text())
        self.orgs = raw.get("orgs", {})
        self.users = raw.get("users", {})
        self.tokens = raw.get("tokens", {})
        self._ensure_demo()
        self._persist()

    def _ensure_demo(self) -> None:
        if DEMO_ORG_ID not in self.orgs:
            self.orgs[DEMO_ORG_ID] = {
                "id": DEMO_ORG_ID,
                "name": "Demo Org",
                "plan": "business",
                "created_at": _utcnow(),
                "usage": {},
            }
        if DEMO_EMAIL not in self.users:
            self.users[DEMO_EMAIL] = {
                "email": DEMO_EMAIL,
                "password_hash": hash_password("demo"),
                "org_id": DEMO_ORG_ID,
                "created_at": _utcnow(),
            }
        if DEMO_TOKEN not in self.tokens:
            self.tokens[DEMO_TOKEN] = {
                "token": DEMO_TOKEN,
                "user_email": DEMO_EMAIL,
                "org_id": DEMO_ORG_ID,
                "created_at": _utcnow(),
            }

    def _persist(self) -> None:
        _data_dir().mkdir(parents=True, exist_ok=True)
        payload = {"orgs": self.orgs, "users": self.users, "tokens": self.tokens}
        _accounts_path().write_text(json.dumps(payload, indent=2))

    def signup(self, email: str, password: str, org_name: str) -> dict[str, Any]:
        key = email.strip().lower()
        if not key or "@" not in key:
            raise ValueError("Valid email required")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        if not org_name.strip():
            raise ValueError("org_name required")
        if key in self.users:
            raise ValueError("Email already registered")

        org_id = f"org_{uuid.uuid4().hex[:12]}"
        token = secrets.token_urlsafe(32)
        now = _utcnow()
        self.orgs[org_id] = {
            "id": org_id,
            "name": org_name.strip(),
            "plan": "free",
            "created_at": now,
            "usage": {},
        }
        self.users[key] = {
            "email": key,
            "password_hash": hash_password(password),
            "org_id": org_id,
            "created_at": now,
        }
        self.tokens[token] = {
            "token": token,
            "user_email": key,
            "org_id": org_id,
            "created_at": now,
        }
        self._persist()
        return {
            "email": key,
            "org_id": org_id,
            "org_name": org_name.strip(),
            "plan": "free",
            "token": token,
        }

    def login(self, email: str, password: str) -> dict[str, Any]:
        key = email.strip().lower()
        user = self.users.get(key)
        if not user or not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid email or password")
        org = self.orgs[user["org_id"]]
        # Issue a fresh API token on each login
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {
            "token": token,
            "user_email": key,
            "org_id": user["org_id"],
            "created_at": _utcnow(),
        }
        self._persist()
        return {
            "email": key,
            "org_id": user["org_id"],
            "org_name": org["name"],
            "plan": org.get("plan", "free"),
            "token": token,
        }

    def resolve_token(self, token: str | None) -> dict[str, Any] | None:
        if not token:
            return None
        entry = self.tokens.get(token)
        if not entry:
            return None
        org = self.orgs.get(entry["org_id"])
        if not org:
            return None
        return {
            "token": token,
            "user_email": entry["user_email"],
            "org_id": entry["org_id"],
            "org": org,
            "plan": org.get("plan", "free"),
        }

    def usage_snapshot(self, org_id: str) -> dict[str, Any]:
        org = self.orgs[org_id]
        plan = org.get("plan", "free")
        month = _month_key()
        used = int(org.get("usage", {}).get(month, {}).get("explains", 0))
        limit = PLAN_EXPLAIN_LIMITS.get(plan, PLAN_EXPLAIN_LIMITS["free"])
        return {
            "org_id": org_id,
            "plan": plan,
            "month": month,
            "explains_used": used,
            "explains_limit": limit,
            "seats_limit": PLAN_SEATS.get(plan, 1),
            "repos_limit": PLAN_REPOS.get(plan, 1),
        }

    def check_explain_quota(self, org_id: str) -> dict[str, Any]:
        snap = self.usage_snapshot(org_id)
        limit = snap["explains_limit"]
        if limit is not None and snap["explains_used"] >= limit:
            return {**snap, "allowed": False}
        return {**snap, "allowed": True}

    def record_explain(self, org_id: str) -> dict[str, Any]:
        org = self.orgs[org_id]
        month = _month_key()
        usage = org.setdefault("usage", {})
        bucket = usage.setdefault(month, {"explains": 0})
        bucket["explains"] = int(bucket.get("explains", 0)) + 1
        self._persist()
        return self.usage_snapshot(org_id)

    def set_plan(self, org_id: str, plan: str) -> dict[str, Any]:
        if plan not in PLAN_EXPLAIN_LIMITS:
            raise ValueError(f"Unknown plan: {plan}")
        self.orgs[org_id]["plan"] = plan
        self._persist()
        return self.usage_snapshot(org_id)


accounts = AccountsStore()
