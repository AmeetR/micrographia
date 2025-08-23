import os, time, random, httpx


class RateLimiter:
    def __init__(self, qps: float | None):
        self.min_interval = 1.0 / qps if qps else 0
        self.last = 0.0

    def wait(self):
        if not self.min_interval:
            return
        dt = time.time() - self.last
        if dt < self.min_interval:
            time.sleep(self.min_interval - dt)
        self.last = time.time()


def ask_openai(prompt: str, model: str, json_only: bool) -> str:
    api = os.getenv("OPENAI_API_KEY")
    if not api:
        raise RuntimeError("OPENAI_API_KEY missing")
    payload = {"model": model, "input": prompt}
    headers = {"Authorization": f"Bearer {api}"}
    with httpx.Client(timeout=60) as c:
        r = c.post("https://api.openai.com/v1/responses", json=payload, headers=headers)
        r.raise_for_status()
        j = r.json()
        return j["output"][0]["content"][0]["text"]


def ask_gemini(prompt: str, model: str, json_only: bool) -> str:
    api = os.getenv("GOOGLE_API_KEY")
    if not api:
        raise RuntimeError("GOOGLE_API_KEY missing")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    with httpx.Client(timeout=60) as c:
        r = c.post(url, json=payload)
        r.raise_for_status()
        j = r.json()
        return j["candidates"][0]["content"]["parts"][0]["text"]


def ask_teacher(provider: str, prompt: str, model: str, json_only: bool, retries: int = 3, qps: float | None = None):
    rl = RateLimiter(qps)
    for i in range(retries):
        try:
            rl.wait()
            text = (
                ask_openai(prompt, model, json_only)
                if provider == "oai"
                else ask_gemini(prompt, model, json_only)
            )
            return text
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 500, 502, 503, 504) and i < retries - 1:
                time.sleep((2**i + random.random()) * 0.5)
                continue
            raise
