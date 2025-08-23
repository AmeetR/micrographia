from symphonia.training.distill import load_student


def test_lora_setup() -> None:
    student = load_student("base", adapter="lora")
    assert student.adapter == "lora"
