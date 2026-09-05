"""Error fingerprinting and normalization for failure clustering."""

from __future__ import annotations

import hashlib
import re

# Strip volatile tokens so the same root cause shares a fingerprint.
_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.I,
)
_HEX = re.compile(r"\b[0-9a-f]{7,40}\b", re.I)
_NUM = re.compile(r"\b\d+\b")
_NUM_UNIT = re.compile(r"\b\d+(?:ms|s|m|h|kb|mb|gb)?\b", re.I)
_PATH_LINE = re.compile(r"(:\d+){1,2}\b")
_WHITESPACE = re.compile(r"\s+")
_QUOTED = re.compile(r"""['"][^'"]{8,}['"]""")


def normalize_error(message: str) -> str:
    """Normalize an error string for stable clustering."""
    text = message.strip().lower()
    text = _UUID.sub("<uuid>", text)
    text = _HEX.sub("<hex>", text)
    text = _NUM_UNIT.sub("<n>", text)
    text = _NUM.sub("<n>", text)
    text = _PATH_LINE.sub(":<n>", text)
    text = _QUOTED.sub("<str>", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return text[:500]


def fingerprint_error(message: str, *, context: str | None = None) -> str:
    """SHA-256 fingerprint of normalized error (+ optional context like job/test name)."""
    normalized = normalize_error(message)
    payload = f"{context or ''}|{normalized}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def extract_primary_error(run_jobs_or_tests: dict) -> tuple[str | None, str | None]:
    """Return (message, context) from a run-like dict with jobs/tests."""
    for test in run_jobs_or_tests.get("tests") or []:
        if test.get("status") in ("failed", "flaky") and test.get("message"):
            return test["message"], f"test:{test.get('name', '')}"
    for job in run_jobs_or_tests.get("jobs") or []:
        if job.get("conclusion") != "failure":
            continue
        for step in job.get("steps") or []:
            if step.get("conclusion") == "failure" and step.get("error_message"):
                return step["error_message"], f"job:{job.get('name', '')}"
        if job.get("name"):
            return f"Job {job['name']} failed", f"job:{job['name']}"
    return None, None
