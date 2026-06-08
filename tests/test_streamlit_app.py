from pathlib import Path


def test_streamlit_dataframes_use_current_width_parameter() -> None:
    source = Path("app.py").read_text(encoding="utf-8")

    assert "use_container_width" not in source
    assert 'width="stretch"' in source
