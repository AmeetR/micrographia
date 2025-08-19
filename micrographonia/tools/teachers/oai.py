"""OpenAI teacher calling the Chat Completions API."""

from __future__ import annotations

import os

import httpx

_API_URL = "https://api.openai.com/v1/chat/completions"


def run(payload: dict) -> dict:
    """Invoke OpenAI with *prompt* and return the text response."""

    prompt = payload["prompt"]
    model = payload.get("model", "gpt-4o-mini")
    api_key = os.environ["OPENAI_API_KEY"]

    headers = {"Authorization": f"Bearer {api_key}"}
    json_payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    response = httpx.post(_API_URL, headers=headers, json=json_payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:  # pragma: no cover - defensive
        raise RuntimeError("unexpected response format") from exc

    return {"text": text}
