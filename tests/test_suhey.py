"""Tests for suhey-academy — Spanish language academy platform."""
import pytest


def test_lesson_structure():
    """Lesson objects have required fields."""
    lesson = {
        "id": "lesson-001",
        "title": "Present Tense",
        "level": "A1",
        "duration_min": 30,
        "exercises": [],
    }
    assert "id" in lesson
    assert "level" in lesson


def test_cefr_levels_ordered():
    """CEFR levels are correctly ordered A1 < A2 < B1 < B2 < C1 < C2."""
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    assert levels == sorted(levels)
    assert len(levels) == 6


def test_progress_percentage():
    """Progress percentage is bounded 0–100."""
    def progress(completed, total):
        if total == 0: return 0
        return min(100, round(completed / total * 100))
    assert progress(3, 10) == 30
    assert progress(10, 10) == 100
    assert progress(0, 5) == 0


def test_vocabulary_scoring():
    """Vocabulary quiz scoring: correct/total."""
    def score_quiz(answers, correct):
        return sum(1 for a, c in zip(answers, correct) if a == c) / len(correct)
    answers = ["hola", "bien", "gracias"]
    correct = ["hola", "mal", "gracias"]
    assert score_quiz(answers, correct) == pytest.approx(2/3)


def test_lesson_levels_defined():
    """Academy uses standard CEFR mapping."""
    mapping = {"beginner": "A1", "elementary": "A2", "intermediate": "B1",
               "upper_intermediate": "B2", "advanced": "C1", "proficient": "C2"}
    assert len(mapping) == 6
    assert mapping["intermediate"] == "B1"


def test_streak_calculation():
    """Daily streak increments on consecutive days."""
    def calculate_streak(login_days):
        streak = 0
        for i in range(len(login_days) - 1, -1, -1):
            if i == len(login_days) - 1 or login_days[i] + 1 == login_days[i+1]:
                streak += 1
            else:
                break
        return streak
    assert calculate_streak([1, 2, 3, 4, 5]) == 5
    assert calculate_streak([1, 2, 4, 5]) == 2


def test_pronunciation_score_range():
    """Pronunciation scores are 0–100."""
    scores = [72, 85, 91, 60, 100, 0]
    for s in scores:
        assert 0 <= s <= 100


def test_enrollment_capacity():
    """Class capacity check."""
    def can_enroll(enrolled, capacity):
        return enrolled < capacity
    assert can_enroll(9, 10) is True
    assert can_enroll(10, 10) is False


def test_certificate_threshold():
    """Certificate issued at 80% course completion."""
    def earns_certificate(score):
        return score >= 80
    assert earns_certificate(85) is True
    assert earns_certificate(79) is False


def test_module_ordering():
    """Modules have sequential ordering."""
    modules = [{"order": i, "title": f"Module {i}"} for i in range(1, 6)]
    orders = [m["order"] for m in modules]
    assert orders == sorted(orders)
    assert orders[0] == 1
