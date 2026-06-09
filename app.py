from __future__ import annotations

from pathlib import Path

import streamlit as st

from themis.pipeline import run_review
from themis.render.markdown_report import render_markdown_report
from themis.ui_rows import context_rows, evidence_gap_rows, risk_rows, verification_rows

SAMPLES = {
    "Safe private certificate rotation": Path("samples/change_safe.md"),
    "Risky public admin exposure": Path("samples/change_risky.md"),
    "Incomplete admin route update": Path("samples/change_incomplete.md"),
}


def main() -> None:
    st.set_page_config(page_title="Themis", page_icon="T", layout="wide")
    st.title("Themis")
    st.write("Read-only reasoning agent for infrastructure change review.")

    review_tab, samples_tab, report_tab, trace_tab, safety_tab = st.tabs(
        ["Review", "Sample scenarios", "Report", "Reasoning trace", "Safety model"]
    )

    if "report" not in st.session_state:
        st.session_state.report = None
        st.session_state.markdown = ""

    with review_tab:
        sample_name = st.selectbox("Sample scenario", list(SAMPLES), index=1)
        context_mode = st.selectbox("Context mode", ["mock", "foundry"], index=0)
        proposal = st.text_area(
            "Change proposal",
            value=SAMPLES[sample_name].read_text(encoding="utf-8"),
            height=320,
        )
        if st.button("Run Themis review", type="primary"):
            try:
                report = run_review(proposal, context_mode=context_mode)
                st.session_state.report = report
                st.session_state.markdown = render_markdown_report(report)
                st.success("Review generated.")
            except Exception as exc:  # noqa: BLE001 - surface setup failures in demo UI.
                st.error(str(exc))

    with samples_tab:
        for name, path in SAMPLES.items():
            st.subheader(name)
            st.markdown(path.read_text(encoding="utf-8"))

    with report_tab:
        report = st.session_state.report
        if report is None:
            st.info("Run a review first.")
        else:
            recommendation_col, confidence_col = st.columns(2)
            recommendation_col.metric("Recommendation", report.recommendation.value)
            confidence_col.metric("Readiness confidence", f"{report.confidence:.2f}")
            st.subheader("Summary")
            st.write(report.summary)
            st.subheader("Risks")
            if report.risks:
                st.dataframe(risk_rows(report), hide_index=True, width="stretch")
            else:
                st.write("No high or medium risks identified from the submitted evidence.")
            st.subheader("Missing evidence")
            if report.evidence_gaps:
                st.dataframe(evidence_gap_rows(report), hide_index=True, width="stretch")
            else:
                st.write("No major evidence gaps identified.")
            st.subheader("Verification plan")
            st.dataframe(verification_rows(report), hide_index=True, width="stretch")
            st.subheader("Rollback questions")
            for question in report.rollback_questions:
                st.write(f"- {question}")
            st.subheader("Retrieved context")
            st.dataframe(context_rows(report), hide_index=True, width="stretch")
            with st.expander("Markdown report"):
                st.markdown(st.session_state.markdown)
            st.download_button(
                "Download markdown report",
                st.session_state.markdown,
                file_name="themis-review.md",
                mime="text/markdown",
            )

    with trace_tab:
        report = st.session_state.report
        if report is None:
            st.info("Run a review first.")
        else:
            for step in report.reasoning_trace:
                st.subheader(step.agent)
                st.write(step.summary)
                st.code(step.output_reference)

    with safety_tab:
        st.markdown(
            """
            - Themis does not deploy infrastructure.
            - Themis does not scan live systems.
            - Themis does not require cloud credentials in mock mode.
            - Themis flags apparent secrets and mutation requests.
            - Guardrail findings prevent a positive recommendation.
            - Themis produces advisory notes for human review, not automatic approval.
            """
        )


if __name__ == "__main__":
    main()
