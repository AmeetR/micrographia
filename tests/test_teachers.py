from unittest.mock import patch

from symphonia.tools.teachers.gemini import run as gemini_run
from symphonia.tools.teachers.oai import run as oai_run


def test_gemini_run(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def fake_post(url, params=None, json=None, timeout=None):
        assert params["key"] == "test-key"
        assert json["contents"][0]["parts"][0]["text"] == "hi"

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "candidates": [
                        {"content": {"parts": [{"text": "hello"}]}}
                    ]
                }

        return Resp()

    with patch("httpx.post", side_effect=fake_post):
        out = gemini_run({"prompt": "hi"})

    assert out == {"text": "hello"}


def test_oai_run(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_post(url, headers=None, json=None, timeout=None):
        assert headers["Authorization"] == "Bearer test-key"
        assert json["messages"][0]["content"] == "hi"

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "choices": [
                        {"message": {"content": "hello"}}
                    ]
                }

        return Resp()

    with patch("httpx.post", side_effect=fake_post):
        out = oai_run({"prompt": "hi"})

    assert out == {"text": "hello"}
