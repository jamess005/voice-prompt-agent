import pytest
from src.confidence import get_score, update_score, pick_by_confidence


def test_get_score_default():
    assert get_score({}, "Maths/Sets") == 0.5


def test_get_score_existing():
    assert get_score({"Maths/Sets": 0.8}, "Maths/Sets") == 0.8


def test_update_correct_increases():
    scores = {"Maths/Sets": 0.5}
    result = update_score(scores, "Maths/Sets", "Correct")
    assert result["Maths/Sets"] == pytest.approx(0.6)


def test_update_incorrect_decreases():
    scores = {"Maths/Sets": 0.5}
    result = update_score(scores, "Maths/Sets", "Incorrect")
    assert result["Maths/Sets"] == pytest.approx(0.4)


def test_update_partial_unchanged():
    scores = {"Maths/Sets": 0.5}
    result = update_score(scores, "Maths/Sets", "Partial")
    assert result["Maths/Sets"] == pytest.approx(0.5)


def test_update_clamps_at_one():
    scores = {"Maths/Sets": 1.0}
    result = update_score(scores, "Maths/Sets", "Correct")
    assert result["Maths/Sets"] == 1.0


def test_update_clamps_at_zero():
    scores = {"Maths/Sets": 0.0}
    result = update_score(scores, "Maths/Sets", "Incorrect")
    assert result["Maths/Sets"] == 0.0


def test_pick_by_confidence_returns_tuple():
    notes = {"Maths": {"Sets": "content"}}
    scores = {}
    subject, topic, content = pick_by_confidence(notes, scores)
    assert subject == "Maths"
    assert topic == "Sets"
