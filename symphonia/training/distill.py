"""Minimal teacher and student models used for testing.

The real project will eventually replace these stubs with calls into Hugging
Face or other model libraries.  For the purposes of unit tests we keep the
behaviour deterministic and very lightweight.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Teacher:
    """Very small stub teacher model.

    The teacher simply returns the input in upper case.  This deterministic
    behaviour makes it easy to write tests without involving heavy models.
    """

    name: str

    def predict(self, text: str) -> str:
        return text.upper()


@dataclass
class Student:
    """Simple student model that memorises teacher outputs."""

    base: str
    adapter: str
    knowledge: dict[str, str] = field(default_factory=dict)

    def predict(self, text: str) -> str:
        """Return the learned output or a lower-cased fallback."""

        return self.knowledge.get(text, text.lower())

    def learn(self, text: str, target: str) -> None:
        """Memorise ``target`` for ``text``."""

        self.knowledge[text] = target


def load_teacher(name: str) -> Teacher:
    """Instantiate a :class:`Teacher` by ``name``."""

    return Teacher(name)


def load_student(base: str, adapter: str) -> Student:
    """Instantiate a :class:`Student` with ``base`` model and ``adapter``."""

    return Student(base=base, adapter=adapter)


def distill_loss(student_out: str, teacher_out: str) -> float:
    """Compute a tiny distillation loss.

    The loss is ``0`` if the student matches the teacher and ``1`` otherwise.
    """

    return 0.0 if student_out == teacher_out else 1.0
