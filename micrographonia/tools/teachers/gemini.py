"""Google Gemini teacher calling the Generative Language API."""

from __future__ import annotations

import os

import httpx

_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def run(payload: dict) -> dict:
    """Invoke Gemini with *prompt* and return the text response.

    Args:
        payload: mapping with at least a ``prompt`` key and optional ``model``.

    Returns:
        dict: ``{"text": <response>}``
    """

    prompt = payload["prompt"]
    model = payload.get("model", "gemini-pro")
    api_key = os.environ["GEMINI_API_KEY"]

    url = _API_URL.format(model=model)
    params = {"key": api_key}
    json_payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = httpx.post(url, params=params, json=json_payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:  # pragma: no cover - defensive
        raise RuntimeError("unexpected response format") from exc

    return {"text": text}
