"""Pydantic models for workflow runs, jobs, tests, and failure signatures."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Step(BaseModel):
    name: str
    conclusion: Literal["success", "failure", "skipped", "cancelled"] | str
    number: int = 0
    duration_seconds: float | None = None
    error_message: str | None = None


class Job(BaseModel):
    id: str
    name: str
    conclusion: Literal["success", "failure", "skipped", "cancelled"] | str
    started_at: str | None = None
    completed_at: str | None = None
    steps: list[Step] = Field(default_factory=list)


class UnitTestResult(BaseModel):
    name: str
    suite: str | None = None
    status: Literal["passed", "failed", "skipped", "flaky"] | str
    duration_ms: float | None = None
    message: str | None = None
    attempt: int = 1


class WorkflowRun(BaseModel):
    id: str
    repository: str
    workflow_name: str
    branch: str
    commit_sha: str
    actor: str | None = None
    event: str | None = None
    status: Literal["completed", "in_progress", "queued"] | str = "completed"
    conclusion: Literal["success", "failure", "cancelled", "skipped"] | str
    created_at: str
    updated_at: str | None = None
    jobs: list[Job] = Field(default_factory=list)
    tests: list[UnitTestResult] = Field(default_factory=list)
    pr_number: int | None = None
    html_url: str | None = None


class FailureSignature(BaseModel):
    fingerprint: str
    normalized_message: str
    sample_message: str
    count: int = 0
    first_seen: str
    last_seen: str
    run_ids: list[str] = Field(default_factory=list)
    job_names: list[str] = Field(default_factory=list)
    test_names: list[str] = Field(default_factory=list)
    branches: list[str] = Field(default_factory=list)


class FlakyTest(BaseModel):
    name: str
    suite: str | None = None
    score: float
    risk: Literal["HIGH", "MED", "LOW"]
    pass_count: int
    fail_count: int
    same_sha_contradictions: int
    retry_recoveries: int
    evidence: list[str] = Field(default_factory=list)


class ExplainResponse(BaseModel):
    run_id: str
    conclusion: str
    deterministic_summary: str
    evidence: list[dict[str, Any]]
    ai_explanation: str | None = None
    related_signatures: list[str] = Field(default_factory=list)
