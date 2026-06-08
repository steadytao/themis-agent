from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from themis.contracts import ReviewReport

RUN_LOG_DIR = Path(".themis/runs")


@dataclass(frozen=True)
class ReviewRunLog:
    path: Path
    created_at: str
    proposal_path: str
    context_mode: str
    recommendation: str


def save_review_run(
    *,
    proposal_path: Path,
    context_mode: str,
    report: ReviewReport,
    markdown: str,
    run_dir: Path = RUN_LOG_DIR,
) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(UTC)
    path = run_dir / _run_filename(created_at, proposal_path)
    data = {
        "created_at": created_at.isoformat().replace("+00:00", "Z"),
        "proposal_path": str(proposal_path),
        "context_mode": context_mode,
        "recommendation": report.recommendation.value,
        "confidence": report.confidence,
        "markdown": markdown,
        "report": _safe_report_dump(report),
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def list_review_runs(run_dir: Path = RUN_LOG_DIR) -> list[ReviewRunLog]:
    if not run_dir.exists():
        return []
    runs: list[ReviewRunLog] = []
    for path in sorted(run_dir.glob("*.json")):
        data = _read_json(path)
        if data is None:
            continue
        runs.append(
            ReviewRunLog(
                path=path,
                created_at=str(data.get("created_at", "")),
                proposal_path=str(data.get("proposal_path", "")),
                context_mode=str(data.get("context_mode", "")),
                recommendation=str(data.get("recommendation", "")),
            )
        )
    return runs


def load_review_run_markdown(path: Path) -> str:
    data = _read_json(path)
    if data is None:
        raise RuntimeError(f"Could not read review run log: {path}")
    markdown = data.get("markdown")
    if not isinstance(markdown, str) or not markdown:
        raise RuntimeError(f"Review run log has no markdown report: {path}")
    return markdown


def _run_filename(created_at: datetime, proposal_path: Path) -> str:
    timestamp = created_at.strftime("%Y%m%dT%H%M%SZ")
    slug = _slug(proposal_path.stem) or "review"
    return f"{timestamp}-{slug}.json"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80]


def _safe_report_dump(report: ReviewReport) -> dict[str, Any]:
    data = report.model_dump(mode="json")
    violations = data.get("guardrail_violations")
    if isinstance(violations, list):
        for index, violation in enumerate(violations):
            if isinstance(violation, dict) and index < len(report.guardrail_violations):
                violation["excerpt"] = report.guardrail_violations[index].redacted_excerpt
    return data


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None
