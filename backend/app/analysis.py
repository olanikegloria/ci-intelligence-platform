"""Deterministic failure clustering and flaky-test heuristics."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from .fingerprint import fingerprint_error, normalize_error
from .models import FailureSignature, FlakyTest, WorkflowRun


def cluster_failures(runs: list[WorkflowRun]) -> list[FailureSignature]:
    clusters: dict[str, dict[str, Any]] = {}

    for run in runs:
        if run.conclusion != "failure":
            # Still cluster failed tests even on overall success? skip for MVP
            pass

        for test in run.tests:
            if test.status not in ("failed", "flaky") or not test.message:
                continue
            fp = fingerprint_error(test.message, context=f"test:{test.name}")
            _accumulate(
                clusters,
                fp,
                message=test.message,
                run=run,
                job_name=None,
                test_name=test.name,
            )

        for job in run.jobs:
            if job.conclusion != "failure":
                continue
            for step in job.steps:
                if step.conclusion != "failure":
                    continue
                msg = step.error_message or f"Step '{step.name}' failed"
                fp = fingerprint_error(msg, context=f"job:{job.name}")
                _accumulate(
                    clusters,
                    fp,
                    message=msg,
                    run=run,
                    job_name=job.name,
                    test_name=None,
                )

    result: list[FailureSignature] = []
    for fp, data in clusters.items():
        result.append(
            FailureSignature(
                fingerprint=fp,
                normalized_message=data["normalized"],
                sample_message=data["sample"],
                count=data["count"],
                first_seen=data["first_seen"],
                last_seen=data["last_seen"],
                run_ids=sorted(data["run_ids"]),
                job_names=sorted(data["job_names"]),
                test_names=sorted(data["test_names"]),
                branches=sorted(data["branches"]),
            )
        )
    return sorted(result, key=lambda c: (-c.count, c.first_seen))


def _accumulate(
    clusters: dict[str, dict[str, Any]],
    fp: str,
    *,
    message: str,
    run: WorkflowRun,
    job_name: str | None,
    test_name: str | None,
) -> None:
    ts = run.created_at
    if fp not in clusters:
        clusters[fp] = {
            "normalized": normalize_error(message),
            "sample": message,
            "count": 0,
            "first_seen": ts,
            "last_seen": ts,
            "run_ids": set(),
            "job_names": set(),
            "test_names": set(),
            "branches": set(),
        }
    c = clusters[fp]
    c["count"] += 1
    c["run_ids"].add(run.id)
    c["branches"].add(run.branch)
    if job_name:
        c["job_names"].add(job_name)
    if test_name:
        c["test_names"].add(test_name)
    if ts < c["first_seen"]:
        c["first_seen"] = ts
    if ts > c["last_seen"]:
        c["last_seen"] = ts


def score_flaky_tests(runs: list[WorkflowRun]) -> list[FlakyTest]:
    """Heuristic flaky score from pass/fail history and same-SHA contradictions."""
    by_test: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "suite": None,
            "pass": 0,
            "fail": 0,
            "by_sha": defaultdict(set),
            "retry_recoveries": 0,
            "evidence": [],
        }
    )

    for run in runs:
        for test in run.tests:
            key = test.name
            bucket = by_test[key]
            bucket["suite"] = test.suite or bucket["suite"]
            status = test.status
            if status == "passed":
                bucket["pass"] += 1
                bucket["by_sha"][run.commit_sha].add("passed")
                if test.attempt > 1:
                    bucket["retry_recoveries"] += 1
                    bucket["evidence"].append(
                        f"Retry recovery on run {run.id} (attempt {test.attempt}, sha {run.commit_sha[:7]})"
                    )
            elif status in ("failed", "flaky"):
                bucket["fail"] += 1
                bucket["by_sha"][run.commit_sha].add("failed")
                if status == "flaky":
                    bucket["evidence"].append(f"Marked flaky on run {run.id}")

    results: list[FlakyTest] = []
    for name, data in by_test.items():
        contradictions = sum(
            1 for statuses in data["by_sha"].values() if "passed" in statuses and "failed" in statuses
        )
        if data["fail"] == 0 and contradictions == 0 and data["retry_recoveries"] == 0:
            continue

        total = data["pass"] + data["fail"]
        fail_rate = data["fail"] / total if total else 0.0
        # Score: same-SHA contradiction heavily weighted; retries and mid fail-rate also
        score = min(
            1.0,
            contradictions * 0.35
            + data["retry_recoveries"] * 0.2
            + (0.3 if 0.05 < fail_rate < 0.7 else 0.0)
            + fail_rate * 0.15,
        )
        if contradictions >= 1 or data["retry_recoveries"] >= 2:
            risk = "HIGH"
        elif score >= 0.35:
            risk = "MED"
        else:
            risk = "LOW"

        if contradictions:
            data["evidence"].append(f"{contradictions} same-SHA pass+fail contradiction(s)")

        results.append(
            FlakyTest(
                name=name,
                suite=data["suite"],
                score=round(score, 3),
                risk=risk,  # type: ignore[arg-type]
                pass_count=data["pass"],
                fail_count=data["fail"],
                same_sha_contradictions=contradictions,
                retry_recoveries=data["retry_recoveries"],
                evidence=data["evidence"][:8],
            )
        )

    return sorted(results, key=lambda t: (-t.score, t.name))


def explain_run(run: WorkflowRun, clusters: list[FailureSignature]) -> dict[str, Any]:
    """Build a deterministic summary with optional stub AI narrative citing evidence."""
    evidence: list[dict[str, Any]] = []
    related: list[str] = []

    failed_jobs = [j for j in run.jobs if j.conclusion == "failure"]
    failed_tests = [t for t in run.tests if t.status in ("failed", "flaky")]

    for job in failed_jobs:
        for step in job.steps:
            if step.conclusion == "failure":
                evidence.append(
                    {
                        "type": "step",
                        "job": job.name,
                        "step": step.name,
                        "message": step.error_message,
                    }
                )

    for test in failed_tests:
        evidence.append(
            {
                "type": "test",
                "name": test.name,
                "status": test.status,
                "message": test.message,
            }
        )

    for cluster in clusters:
        if run.id in cluster.run_ids:
            related.append(cluster.fingerprint)

    if run.conclusion == "success":
        summary = (
            f"Run {run.id} on {run.branch}@{run.commit_sha[:7]} completed successfully "
            f"({len(run.jobs)} job(s), {len(run.tests)} test result(s))."
        )
    else:
        parts = [
            f"Run {run.id} failed on branch `{run.branch}` (commit {run.commit_sha[:7]}).",
        ]
        if failed_jobs:
            parts.append(
                f"Failed job(s): {', '.join(j.name for j in failed_jobs)}."
            )
        if failed_tests:
            parts.append(
                f"Failed/flaky test(s): {', '.join(t.name for t in failed_tests)}."
            )
        if related:
            parts.append(
                f"Matches {len(related)} known failure signature(s): {', '.join(related[:3])}."
            )
        else:
            parts.append("No prior matching failure signature in the store.")
        if run.pr_number:
            parts.append(f"Associated with PR #{run.pr_number}.")
        summary = " ".join(parts)

    ai = _ai_explanation(run, evidence, related, summary)

    # Quarantine recommendations for flaky tests in this run
    quarantine = []
    for test in run.tests:
        if test.status == "flaky" or (
            test.status == "failed" and any(
                c for c in clusters if run.id in c.run_ids and test.name in (c.sample_message or "")
            )
        ):
            quarantine.append(
                {
                    "test": test.name,
                    "action": "quarantine_non_blocking",
                    "reason": "Intermittent or signature-matched failure — keep running but do not block merges until stable",
                    "owner_hint": run.actor or "unassigned",
                }
            )

    return {
        "run_id": run.id,
        "conclusion": run.conclusion,
        "deterministic_summary": summary,
        "evidence": evidence,
        "ai_explanation": ai["text"],
        "ai_provider": ai["provider"],
        "ai_model": ai.get("model"),
        "related_signatures": related,
        "quarantine_recommendations": quarantine,
    }


def _ai_explanation(
    run: WorkflowRun,
    evidence: list[dict[str, Any]],
    related: list[str],
    summary: str,
) -> dict[str, Any]:
    from . import ollama_client

    evidence_blob = json.dumps(
        {
            "summary": summary,
            "run": {
                "id": run.id,
                "branch": run.branch,
                "commit": run.commit_sha,
                "pr": run.pr_number,
                "conclusion": run.conclusion,
            },
            "evidence": evidence,
            "related_signatures": related,
        },
        indent=2,
    )
    result = ollama_client.grounded_complete(
        task=(
            "Explain the likely CI failure cause and whether it may recur. "
            "Recommend quarantine only if evidence shows flakiness. "
            "Cite only evidence fields present below."
        ),
        evidence=evidence_blob,
    )
    if result.get("ok") and result.get("text"):
        return {
            "text": result["text"],
            "provider": result.get("provider"),
            "model": result.get("model"),
        }
    return {
        "text": _fallback_explanation(run, evidence, related),
        "provider": "fallback",
        "model": None,
    }


def _fallback_explanation(
    run: WorkflowRun,
    evidence: list[dict[str, Any]],
    related: list[str],
) -> str:
    """Deterministic narrative when Ollama is unavailable."""
    if run.conclusion == "success":
        return (
            f"Run `{run.id}` succeeded. No failure evidence to explain. "
            f"Cited: run_id={run.id}, commit={run.commit_sha[:7]}."
        )

    cites: list[str] = [f"run_id={run.id}", f"commit={run.commit_sha[:7]}"]
    for e in evidence[:4]:
        if e["type"] == "test":
            cites.append(f"test={e['name']}")
        else:
            cites.append(f"step={e.get('job')}/{e.get('step')}")
    for sig in related[:3]:
        cites.append(f"signature={sig}")

    bullets = []
    for e in evidence[:5]:
        msg = (e.get("message") or "no message")[:120]
        if e["type"] == "test":
            bullets.append(f"- Test `{e['name']}` ({e['status']}): {msg}")
        else:
            bullets.append(f"- Step `{e.get('job')}` / `{e.get('step')}`: {msg}")

    body = "\n".join(bullets) if bullets else "- No structured evidence rows."
    return (
        f"Based on stored facts for run `{run.id}`:\n{body}\n"
        f"Evidence citations: {', '.join(cites)}."
    )
