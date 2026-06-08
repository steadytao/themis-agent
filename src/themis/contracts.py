from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Recommendation(StrEnum):
    APPROVE_WITH_CONDITIONS = "APPROVE WITH CONDITIONS"
    REVIEW_REQUIRED = "REVIEW REQUIRED"
    DO_NOT_PROCEED_YET = "DO NOT PROCEED YET"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"


class ChangeProposal(BaseModel):
    title: str
    service: str = "unknown"
    environment: str = "unknown"
    change_type: str = "unknown"
    summary: str
    affected_components: list[str] = Field(default_factory=list)
    network_exposure: str = "unknown"
    identity_changes: str = "unknown"
    data_sensitivity: str = "unknown"
    deployment_window: str = "unknown"
    rollback_plan: str = "unknown"
    provided_evidence: list[str] = Field(default_factory=list)
    raw_text: str


class RetrievedContext(BaseModel):
    source_id: str
    title: str
    kind: str
    relevant_excerpt: str
    reason_used: str
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[str] = Field(default_factory=list)


class RiskFinding(BaseModel):
    category: str
    severity: Literal["low", "medium", "high"]
    claim: str
    evidence: str
    assumption: str | None = None
    impact: str
    suggested_mitigation: str


class EvidenceGap(BaseModel):
    missing_item: str
    why_it_matters: str
    blocking_level: Literal["advisory", "conditional", "blocking"]
    question_for_owner: str


class VerificationStep(BaseModel):
    phase: Literal["pre-change", "post-change", "rollback"]
    step: str
    expected_result: str
    failure_action: str


class GuardrailViolation(BaseModel):
    kind: str
    reason: str
    excerpt: str

    @property
    def redacted_excerpt(self) -> str:
        if "=" in self.excerpt:
            name = self.excerpt.split("=", 1)[0]
            return f"{name}=[REDACTED]"
        return "[REDACTED]"


class ReasoningTraceStep(BaseModel):
    agent: str
    summary: str
    output_reference: str


class ReviewReport(BaseModel):
    recommendation: Recommendation
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    facts: list[str]
    assumptions: list[str]
    retrieved_context: list[RetrievedContext]
    risks: list[RiskFinding]
    evidence_gaps: list[EvidenceGap]
    verification_steps: list[VerificationStep]
    rollback_questions: list[str]
    human_review_notes: list[str]
    reasoning_trace: list[ReasoningTraceStep]
    guardrail_violations: list[GuardrailViolation] = Field(default_factory=list)

    @field_validator("human_review_notes")
    @classmethod
    def require_human_review_note(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("human_review_notes must not be empty")
        joined = " ".join(value).lower()
        if "human" not in joined:
            raise ValueError("human_review_notes must mention human review")
        return value
