from __future__ import annotations

import re

from themis.contracts import ChangeProposal, EvidenceGap, RiskFinding


def find_evidence_gaps(proposal: ChangeProposal, risks: list[RiskFinding]) -> list[EvidenceGap]:
    del risks
    lower = proposal.raw_text.lower()
    gaps: list[EvidenceGap] = []

    if proposal.identity_changes in {"missing or unclear", "unknown"} and (
        proposal.network_exposure == "public" or proposal.data_sensitivity == "sensitive"
    ):
        gaps.append(
            EvidenceGap(
                missing_item="Authentication model",
                why_it_matters="Public or administrative access must not rely on unclear identity controls.",
                blocking_level="blocking",
                question_for_owner="Which identity provider, policy and negative-access test prove unauthorised access is denied?",
            )
        )

    if proposal.rollback_plan == "unknown":
        gaps.append(
            EvidenceGap(
                missing_item="Rollback plan",
                why_it_matters="Reviewers need to know how the previous routing state can be restored.",
                blocking_level="blocking",
                question_for_owner="What exact rollback steps and success checks will be used?",
            )
        )

    if not _has_positive_evidence(lower, "owner approval"):
        gaps.append(
            EvidenceGap(
                missing_item="Owner approval",
                why_it_matters="The service owner should accept the exposure and operational risk.",
                blocking_level="conditional",
                question_for_owner="Which owner approved this change and where is that recorded?",
            )
        )

    if proposal.network_exposure == "public" and not any(
        _has_positive_evidence(lower, term) for term in ["source range", "cidr", "allowed ip"]
    ):
        gaps.append(
            EvidenceGap(
                missing_item="Approved source ranges",
                why_it_matters="A public endpoint needs explicit reachability boundaries.",
                blocking_level="blocking",
                question_for_owner="Which source ranges are allowed, and who approved them?",
            )
        )

    if not any(_has_positive_evidence(lower, term) for term in ["health check", "post-change", "verification"]):
        gaps.append(
            EvidenceGap(
                missing_item="Post-change verification",
                why_it_matters="A working-looking deployment can still expose the wrong path or fail negative checks.",
                blocking_level="conditional",
                question_for_owner="What health, access-denial, log and alert checks will be run after the change?",
            )
        )

    return gaps


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
