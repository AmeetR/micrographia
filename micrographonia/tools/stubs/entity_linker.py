def run(payload: dict) -> dict:
    entities = [{"mention": m, "entity": m.lower()} for m in payload["mentions"]]
    return {"entities": entities}
