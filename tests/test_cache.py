from micrographonia.runtime.cache import cache_key


def test_cache_key_stability() -> None:
    key1 = cache_key("tool", "1", {"a": 1, "b": 2}, "mhash")
    key2 = cache_key("tool", "1", {"b": 2, "a": 1}, "mhash")
    key3 = cache_key("tool", "2", {"a": 1, "b": 2}, "mhash")
    key4 = cache_key("tool", "1", {"a": 1, "b": 2}, "other")
    assert key1 == key2
    assert key1 != key3
    assert key1 != key4
