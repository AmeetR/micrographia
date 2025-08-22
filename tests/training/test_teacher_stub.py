from symphonia.training.distill import load_teacher


def test_teacher_stub() -> None:
    teacher = load_teacher("dummy")
    assert teacher.predict("hello") == "HELLO"
