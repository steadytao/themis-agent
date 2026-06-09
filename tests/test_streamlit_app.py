from pathlib import Path


def test_streamlit_dataframes_use_current_width_parameter() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert "use_container_width" not in source
    assert 'width="stretch"' in source


def test_streamlit_report_tab_exposes_linear_markdown_report() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert '["Review", "Sample scenarios", "Report", "Reasoning trace", "Safety model"]' in source
    assert 'st.text_area("Markdown report"' in source


def test_streamlit_report_tab_exposes_markdown_download() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert 'st.download_button(' in source
    assert '"Download markdown report"' in source
    assert 'file_name="themis-review.md"' in source
    assert 'mime="text/markdown"' in source
