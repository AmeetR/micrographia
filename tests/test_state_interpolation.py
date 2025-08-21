from __future__ import annotations

import pytest

from symphonia.runtime.state import State, interpolate
from symphonia.runtime.errors import SchemaError


def test_interpolation() -> None:
    state = State({"foo": "bar"}, {"x": 1})
    state["nodes"]["n1"] = {"a": 2}
    data = {"a": "${context.foo}", "b": "${vars.x}", "c": "${n1.a}"}
    assert interpolate(data, state) == {"a": "bar", "b": 1, "c": 2}


def test_missing_ref() -> None:
    state = State({}, {})
    with pytest.raises(SchemaError):
        interpolate("${unknown}", state)
