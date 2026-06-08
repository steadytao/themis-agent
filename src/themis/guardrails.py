from __future__ import annotations

import re

from pydantic import BaseModel, Field

from themis.contracts import GuardrailViolation


SECRET_PATTERNS = [
    re.compile(r"\b(?:api[_-]?key|token|password|secret)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
]

MUTATION_PATTERNS = [
    re.compile(r"\bdeploy\s+(?:this|the|it|now|to|into|with)\b", re.IGNORECASE),
    re.compile(r"\bapply\b.+\bterraform\b", re.IGNORECASE),
    re.compile(r"\bscan live\b", re.IGNORECASE),
    re.compile(r"\bexploit\b", re.IGNORECASE),
    re.compile(r"\bbypass approval\b", re.IGNORECASE),
    re.compile(r"\bsuppress logging\b", re.IGNORECASE),
    re.compile(r"\bhide (?:the )?risk\b", re.IGNORECASE),
]


class GuardrailResult(BaseModel):
    blocked: bool
    reasons: list[str] = Field(default_factory=list)
    violations: list[GuardrailViolation] = Field(default_factory=list)


def inspect_input(text: str) -> GuardrailResult:
    violations: list[GuardrailViolation] = []

    for pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            violations.append(
                GuardrailViolation(
                    kind="secret",
                    reason="Input appears to contain secret or credential material.",
                    excerpt=match.group(0),
                )
            )

    for pattern in MUTATION_PATTERNS:
        for match in pattern.finditer(text):
            violations.append(
                GuardrailViolation(
                    kind="mutation",
                    reason="Input asks Themis to perform or assist a mutation instead of review.",
                    excerpt=match.group(0),
                )
            )

    return GuardrailResult(
        blocked=bool(violations),
        reasons=[violation.reason for violation in violations],
        violations=violations,
    )
