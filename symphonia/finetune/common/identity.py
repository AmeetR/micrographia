import hashlib, unicodedata, orjson


def _norm(x):
    if isinstance(x, str):
        return unicodedata.normalize("NFC", x)
    if isinstance(x, list):
        return [_norm(i) for i in x]
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in x.items()}
    return x


def _minify(obj: dict) -> bytes:
    return orjson.dumps(_norm(obj), option=orjson.OPT_SORT_KEYS)


def stable_id(rec: dict) -> str:
    payload = {"input": rec.get("input", {}), "target": rec.get("target", {})}
    h = hashlib.sha256(_minify(payload)).hexdigest()
    return h[:16]


def bucket_of_id(id_: str) -> int:
    return int(hashlib.sha1(id_.encode()).hexdigest(), 16) % 100


def split_for_id(id_: str) -> str:
    b = bucket_of_id(id_)
    return "train" if b < 90 else "val" if b < 95 else "test"
