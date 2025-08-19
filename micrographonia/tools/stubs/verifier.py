def run(payload: dict) -> dict:
    triples = [[e["entity"], "is", e["mention"]] for e in payload["entities"]]
    return {"triples": triples}
