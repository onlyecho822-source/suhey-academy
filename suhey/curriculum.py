"""
suhey/curriculum.py — Suhey Spanish Academy Curriculum Engine.
Manages course structure, student progress, vocabulary scoring,
CEFR level tracking, and certificate issuance.
∇θ Operator — Echo Universe T2 Revenue
"""
from __future__ import annotations
import hashlib, time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class CEFRLevel(Enum):
    A1 = 1   # Beginner
    A2 = 2   # Elementary
    B1 = 3   # Intermediate
    B2 = 4   # Upper Intermediate
    C1 = 5   # Advanced
    C2 = 6   # Proficient


class LessonType(Enum):
    VOCABULARY   = "vocabulary"
    GRAMMAR      = "grammar"
    CONVERSATION = "conversation"
    CULTURE      = "culture"
    PRONUNCIATION = "pronunciation"


CERTIFICATE_THRESHOLD = 0.80  # 80% course completion required


@dataclass
class Lesson:
    lesson_id: str
    title: str
    level: CEFRLevel
    lesson_type: LessonType
    duration_min: int = 30
    exercises: List[dict] = field(default_factory=list)

    def add_exercise(self, question: str, answer: str, points: int = 1) -> None:
        self.exercises.append({"q": question, "a": answer, "points": points})

    def max_points(self) -> int:
        return sum(e["points"] for e in self.exercises)


@dataclass
class StudentRecord:
    student_id: str
    name: str
    current_level: CEFRLevel = CEFRLevel.A1
    enrolled_at: float = field(default_factory=time.time)
    completed_lessons: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    streak_days: int = 0
    certificates: List[str] = field(default_factory=list)

    def progress(self, total_lessons: int) -> float:
        if total_lessons == 0:
            return 0.0
        return min(1.0, len(self.completed_lessons) / total_lessons)

    def average_score(self) -> float:
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)

    def earns_certificate(self, total_lessons: int) -> bool:
        return self.progress(total_lessons) >= CERTIFICATE_THRESHOLD


class VocabularyScorer:
    """Score vocabulary quiz responses."""

    @staticmethod
    def score_quiz(answers: List[str], correct: List[str]) -> float:
        """Returns fraction correct (0.0–1.0)."""
        if not correct:
            return 0.0
        hits = sum(1 for a, c in zip(answers, correct) if a.lower().strip() == c.lower().strip())
        return hits / len(correct)

    @staticmethod
    def pronunciation_score(audio_score_raw: float) -> int:
        """Normalize raw pronunciation score to 0–100."""
        return max(0, min(100, round(audio_score_raw * 100)))


class AcademyCurriculum:
    """Manages the full course catalog and student progress."""

    def __init__(self, academy_name: str = "Suhey Spanish Academy"):
        self.academy_name = academy_name
        self._lessons: Dict[str, Lesson] = {}
        self._students: Dict[str, StudentRecord] = {}

    def add_lesson(self, lesson: Lesson) -> None:
        self._lessons[lesson.lesson_id] = lesson

    def enroll(self, student_id: str, name: str) -> StudentRecord:
        record = StudentRecord(student_id=student_id, name=name)
        self._students[student_id] = record
        return record

    def complete_lesson(self, student_id: str, lesson_id: str, score: float) -> bool:
        if student_id not in self._students or lesson_id not in self._lessons:
            return False
        student = self._students[student_id]
        if lesson_id not in student.completed_lessons:
            student.completed_lessons.append(lesson_id)
        student.scores[lesson_id] = score
        return True

    def issue_certificate(self, student_id: str) -> Optional[str]:
        student = self._students.get(student_id)
        if not student:
            return None
        if student.earns_certificate(len(self._lessons)):
            cert_id = f"CERT-{student_id}-{int(time.time())}"
            student.certificates.append(cert_id)
            return cert_id
        return None

    def leaderboard(self) -> List[tuple]:
        ranked = sorted(
            [(s.name, s.average_score()) for s in self._students.values()],
            key=lambda x: x[1], reverse=True
        )
        return ranked

    def lesson_count(self) -> int:
        return len(self._lessons)

    def student_count(self) -> int:
        return len(self._students)

    def status(self) -> Dict:
        return {
            "academy": self.academy_name,
            "lessons": self.lesson_count(),
            "students": self.student_count(),
            "certificate_threshold": CERTIFICATE_THRESHOLD,
        }
