from __future__ import annotations

import argparse
import sys
from pathlib import Path

from themis.pipeline import run_review
from themis.render.markdown_report import render_markdown_report
from themis.run_logs import list_review_runs, load_review_run_markdown, save_review_run


def main() -> None:
    _configure_stdout()
    parser = argparse.ArgumentParser(description="Run a Themis infrastructure change review.")
    parser.add_argument("proposal", type=Path, nargs="?", help="Path to a markdown change proposal.")
    parser.add_argument("--context-mode", choices=["mock", "foundry"], default="mock")
    parser.add_argument("--list-runs", action="store_true", help="List saved local review logs.")
    parser.add_argument("--show-run", type=Path, help="Print a saved review log's markdown report.")
    args = parser.parse_args()

    if args.list_runs:
        _print_run_list()
        return

    if args.show_run is not None:
        print(load_review_run_markdown(args.show_run), end="")
        return

    if args.proposal is None:
        parser.error("proposal is required unless --list-runs or --show-run is used")

    report = run_review(args.proposal.read_text(encoding="utf-8"), context_mode=args.context_mode)
    markdown = render_markdown_report(report)
    print(markdown)
    run_log = save_review_run(
        proposal_path=args.proposal,
        context_mode=args.context_mode,
        report=report,
        markdown=markdown,
    )
    print(f"Saved review log: {run_log}")


def _print_run_list() -> None:
    runs = list_review_runs()
    if not runs:
        print("No saved review logs.")
        return
    for run in runs:
        print(
            f"{run.path} | {run.created_at} | {run.context_mode} | "
            f"{run.recommendation} | {run.proposal_path}"
        )


def _configure_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        return


if __name__ == "__main__":
    main()
