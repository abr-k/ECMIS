"""Checks that analyst reviews are saved and survive a 'restart' (a fresh connection)."""
import pytest

from src.storage import load_reviews, save_review


def test_nothing_saved_yet(tmp_path):
    assert load_reviews(tmp_path / "t.db") == {}


def test_save_then_load_and_update(tmp_path):
    db = tmp_path / "t.db"
    save_review("AAA-20260105", "Under Review", "  looking into it ", db)
    assert load_reviews(db) == {"AAA-20260105": {"status": "Under Review", "note": "looking into it"}}
    save_review("AAA-20260105", "Closed", "", db)  # saving again replaces the old review
    assert load_reviews(db) == {"AAA-20260105": {"status": "Closed", "note": ""}}


def test_invalid_status_is_refused(tmp_path):
    with pytest.raises(ValueError):
        save_review("AAA-20260105", "Guilty", "", tmp_path / "t.db")


def test_notes_with_quotes_and_markup_are_stored_literally(tmp_path):
    db = tmp_path / "t.db"
    save_review("A-1", "New", "it's <b>odd</b>'; DROP TABLE alert_review;--", db)
    assert load_reviews(db)["A-1"]["note"] == "it's <b>odd</b>'; DROP TABLE alert_review;--"
