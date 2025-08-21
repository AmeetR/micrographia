import time
from symphonia.runtime.cache import cache_key, SimpleCache


def test_cache_key_stability() -> None:
    key1 = cache_key("tool", "1", {"a": 1, "b": 2}, "mhash")
    key2 = cache_key("tool", "1", {"b": 2, "a": 1}, "mhash")
    key3 = cache_key("tool", "2", {"a": 1, "b": 2}, "mhash")
    key4 = cache_key("tool", "1", {"a": 1, "b": 2}, "other")
    assert key1 == key2
    assert key1 != key3
    assert key1 != key4


def test_cache_eviction(tmp_path) -> None:
    cache = SimpleCache(tmp_path, max_bytes=20)
    cache.write("a", {"v": "a"})
    time.sleep(0.01)
    cache.write("b", {"v": "b"})
    time.sleep(0.01)
    cache.write("c", {"v": "c"})
    files = {p.name for p in tmp_path.glob("*.json")}
    assert "a.json" not in files  # oldest evicted
    assert "b.json" in files and "c.json" in files
