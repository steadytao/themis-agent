from __future__ import annotations

from typing import Literal

from themis.agents.evidence_gap import find_evidence_gaps
from themis.agents.intake import parse_change_proposal
from themis.agents.report import build_review_report
from themis.agents.risk import analyse_risks
from themis.agents.verification import plan_verification
from themis.contracts import ReviewReport
from themis.guardrails import inspect_input
from themis.iq import retrieve_context


def run_review(proposal_text: str, context_mode: Literal["mock", "foundry"] = "mock") -> ReviewReport:
    guardrails = inspect_input(proposal_text)
    proposal = parse_change_proposal(proposal_text)
    context = retrieve_context(proposal.raw_text, mode=context_mode)
    risks = analyse_risks(proposal, context)
    gaps = find_evidence_gaps(proposal, risks)
    verification = plan_verification(proposal, risks, gaps)
    return build_review_report(
        proposal=proposal,
        context=context,
        risks=risks,
        gaps=gaps,
        verification=verification,
        guardrail_violations=guardrails.violations,
    )
