"""Evaluation utilities for student models.

The functions here compare a distilled student model against its teacher on a
dataset and compute a handful of simple metrics.  They are intentionally
minimal to keep tests fast.
"""

from __future__ import annotations

from typing import Iterable

from symphonia.training.distill import Teacher, Student


def evaluate(student: Student, teacher: Teacher, data: Iterable[dict]) -> dict:
    """Evaluate ``student`` on ``data`` and compute simple metrics."""

    total = 0
    correct = 0
    for item in data:
        inp = item["input"]
        expected = item.get("target") or teacher.predict(inp)
        pred = student.predict(inp)
        if pred == expected:
            correct += 1
        total += 1
    accuracy = correct / total if total else 0.0
    metrics = {
        "accuracy": accuracy,
        "f1": accuracy,  # in this tiny setting precision=recall=accuracy
        "loss": 1.0 - accuracy,
        "student_vs_teacher_agreement": accuracy,
    }
    return metrics
