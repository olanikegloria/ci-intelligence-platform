"""Tests for error fingerprinting and failure clustering."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.analysis import cluster_failures, score_flaky_tests
from app.fingerprint import fingerprint_error, normalize_error
from app.models import Job, Step, UnitTestResult, WorkflowRun


def test_normalize_strips_uuids_and_numbers():
    a = normalize_error(
        "TimeoutError: connection timed out after 5000ms (uuid=3fa85f64-5717-4562-b3fc-2c963f66afa6)"
    )
    b = normalize_error(
        "TimeoutError: connection timed out after 8000ms (uuid=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)"
    )
    assert a == b
    assert "<uuid>" in a
    assert "<n>" in a


def test_fingerprint_stable_across_volatile_tokens():
    msg1 = "AssertionError: expected status 200, got 500 at payments/test_charge.py:88"
    msg2 = "AssertionError: expected status 200, got 500 at payments/test_charge.py:91"
    assert fingerprint_error(msg1, context="test:charge") == fingerprint_error(
        msg2, context="test:charge"
    )
    assert fingerprint_error(msg1, context="test:a") != fingerprint_error(
        msg1, context="test:b"
    )


def test_cluster_groups_same_root_cause():
    runs = [
        WorkflowRun(
            id="r1",
            repository="acme/x",
            workflow_name="CI",
            branch="main",
            commit_sha="aaa1111111111111111111111111111111111111",
            conclusion="failure",
            created_at="2026-03-01T00:00:00Z",
            jobs=[
                Job(
                    id="j1",
                    name="test",
                    conclusion="failure",
                    steps=[
                        Step(
                            name="Run",
                            conclusion="failure",
                            number=1,
                            error_message="TimeoutError: redis timeout 5000ms uuid=11111111-1111-1111-1111-111111111111",
                        )
                    ],
                )
            ],
            tests=[],
        ),
        WorkflowRun(
            id="r2",
            repository="acme/x",
            workflow_name="CI",
            branch="main",
            commit_sha="bbb2222222222222222222222222222222222222",
            conclusion="failure",
            created_at="2026-03-02T00:00:00Z",
            jobs=[
                Job(
                    id="j2",
                    name="test",
                    conclusion="failure",
                    steps=[
                        Step(
                            name="Run",
                            conclusion="failure",
                            number=1,
                            error_message="TimeoutError: redis timeout 9000ms uuid=22222222-2222-2222-2222-222222222222",
                        )
                    ],
                )
            ],
            tests=[],
        ),
    ]
    clusters = cluster_failures(runs)
    assert len(clusters) == 1
    assert clusters[0].count == 2
    assert clusters[0].first_seen.startswith("2026-03-01")
    assert clusters[0].last_seen.startswith("2026-03-02")
    assert set(clusters[0].run_ids) == {"r1", "r2"}


def test_flaky_score_detects_same_sha_contradiction():
    sha = "cccccccccccccccccccccccccccccccccccccccc"
    runs = [
        WorkflowRun(
            id="a",
            repository="acme/x",
            workflow_name="CI",
            branch="main",
            commit_sha=sha,
            conclusion="failure",
            created_at="2026-03-01T00:00:00Z",
            jobs=[],
            tests=[
                UnitTestResult(name="flaky_one", status="failed", message="boom", attempt=1),
            ],
        ),
        WorkflowRun(
            id="b",
            repository="acme/x",
            workflow_name="CI",
            branch="main",
            commit_sha=sha,
            conclusion="success",
            created_at="2026-03-01T01:00:00Z",
            jobs=[],
            tests=[
                UnitTestResult(name="flaky_one", status="passed", attempt=2),
            ],
        ),
    ]
    flaky = score_flaky_tests(runs)
    assert len(flaky) == 1
    assert flaky[0].name == "flaky_one"
    assert flaky[0].same_sha_contradictions == 1
    assert flaky[0].risk == "HIGH"
    assert flaky[0].score > 0.3
