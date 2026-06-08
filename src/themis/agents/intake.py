from __future__ import annotations

import re

from themis.contracts import ChangeProposal


def parse_change_proposal(text: str) -> ChangeProposal:
    title = _title(text)
    lower = text.lower()
    service = _after_label(text, "service") or _infer_service(lower)
    environment = _after_label(text, "environment") or _infer_environment(lower)
    rollback = _after_label(text, "rollback") or ("provided" if _has_positive_evidence(lower, "rollback") else "unknown")

    return ChangeProposal(
        title=title,
        service=service,
        environment=environment,
        change_type=_infer_change_type(lower),
        summary=_summary(text),
        affected_components=_components(lower),
        network_exposure=_network_exposure(lower),
        identity_changes=_identity_changes(lower),
        data_sensitivity=_data_sensitivity(lower),
        deployment_window=_deployment_window(lower),
        rollback_plan=rollback,
        provided_evidence=_provided_evidence(lower),
        raw_text=text.strip(),
    )


def _title(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean.startswith("#"):
            return clean.lstrip("# ").strip()
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            return clean[:90]
    return "Untitled change"


def _after_label(text: str, label: str) -> str | None:
    match = re.search(rf"^{label}\s*:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _summary(text: str) -> str:
    body = " ".join(line.strip("# ").strip() for line in text.splitlines() if line.strip())
    return body[:300]


def _infer_service(lower: str) -> str:
    if "admin" in lower:
        return "admin service"
    if "payments" in lower:
        return "payments service"
    return "infrastructure service"


def _infer_environment(lower: str) -> str:
    if "production" in lower or "prod" in lower:
        return "production"
    if "staging" in lower:
        return "staging"
    return "unknown"


def _infer_change_type(lower: str) -> str:
    if "certificate" in lower and ("rotate" in lower or "rotation" in lower):
        return "certificate rotation"
    if "public" in lower or "load balancer" in lower or "application gateway" in lower:
        return "network exposure"
    if "database" in lower:
        return "database"
    return "configuration"


def _components(lower: str) -> list[str]:
    components = []
    for label in ["application gateway", "load balancer", "network security group", "tls", "logging", "database", "dns"]:
        if label in lower:
            components.append(label)
    return components or ["unspecified"]


def _network_exposure(lower: str) -> str:
    if "public" in lower or "internet" in lower:
        return "public"
    if "private" in lower or "internal" in lower:
        return "internal"
    return "unknown"


def _identity_changes(lower: str) -> str:
    if "authentication will be added later" in lower or "unclear authentication" in lower:
        return "missing or unclear"
    if "managed identity" in lower or "entra" in lower or "mfa" in lower:
        return "specified"
    return "unknown"


def _data_sensitivity(lower: str) -> str:
    if "customer" in lower or "personal" in lower or "admin" in lower:
        return "sensitive"
    return "unknown"


def _deployment_window(lower: str) -> str:
    if "business hours" in lower:
        return "business hours"
    if "maintenance window" in lower or "after hours" in lower:
        return "maintenance window"
    return "unknown"


def _provided_evidence(lower: str) -> list[str]:
    evidence = []
    for item in ["owner approval", "rollback", "health check", "monitoring", "source range", "certificate"]:
        if _has_positive_evidence(lower, item):
            evidence.append(item)
    return evidence


def _has_positive_evidence(lower: str, item: str) -> bool:
    if item not in lower:
        return False
    if re.search(rf"\bno\b[^.]*\b{re.escape(item)}\b", lower):
        return False
    negated_patterns = [
        f"no {item}",
        f"not include {item}",
        f"does not list {item}",
        f"does not include {item}",
        f"without {item}",
        f"missing {item}",
    ]
    return not any(pattern in lower for pattern in negated_patterns)
