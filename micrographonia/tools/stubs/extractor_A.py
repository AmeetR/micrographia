def run(payload: dict) -> dict:
    text: str = payload["text"]
    mentions = [w for w in text.split() if w and w[0].isupper()]
    return {"mentions": mentions}
