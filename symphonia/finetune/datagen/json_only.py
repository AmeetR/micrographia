import json, re

FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

def strip_fences(text: str) -> str:
    return FENCE_RE.sub("", text).strip()


def extract_first_json(text: str):
    s = strip_fences(text)
    try:
        return True, json.loads(s), None
    except Exception:
        pass
    for opener, closer in [("{", "}"), ("[", "]")]:
        depth = 0
        start = -1
        for i, ch in enumerate(s):
            if ch == opener:
                if depth == 0:
                    start = i
                depth += 1
            elif ch == closer and depth:
                depth -= 1
                if depth == 0 and start >= 0:
                    frag = s[start : i + 1]
                    try:
                        return True, json.loads(frag), None
                    except Exception:
                        pass
    return False, None, "no valid json found"
