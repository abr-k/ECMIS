"""Runs the real Streamlit app headlessly. Skipped automatically if streamlit or plotly is not installed."""
from pathlib import Path

import pytest

pytest.importorskip("plotly")
pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from src import storage  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DEFAULT_DB", tmp_path / "test.db")  # never touch the real database
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    return at


@pytest.mark.parametrize("page", ["Dashboard", "Market Analysis", "Alerts"])
def test_each_page_shows_without_errors_and_with_the_disclaimer(app, page):
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception
    assert any("Independent educational prototype" in w.value for w in app.warning)


def test_saving_a_review_persists(app):
    app.sidebar.radio[0].set_value("Alerts").run()
    chosen = next(s for s in app.selectbox if s.label == "Choose an alert").value
    next(s for s in app.selectbox if s.label == "Status of this alert").select("Under Review")
    next(t for t in app.text_area if t.label.startswith("Note")).input("checking the news")
    next(b for b in app.button if b.label == "Save review").click().run()
    assert not app.exception
    assert storage.load_reviews()[chosen] == {"status": "Under Review", "note": "checking the news"}
