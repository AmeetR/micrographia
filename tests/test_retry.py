from micrographonia.runtime.retry import RetryMatcher, backoff_delays
from micrographonia.runtime.errors import ToolCallError, SchemaError


def test_retry_matcher() -> None:
    matcher = RetryMatcher(["ToolCallError:429", "ToolCallError:5xx"])
    assert matcher.matches(ToolCallError(status=429))
    assert matcher.matches(ToolCallError(status=502))
    assert not matcher.matches(SchemaError("boom", stage="POST"))


def test_backoff_sequence() -> None:
    delays = backoff_delays(retries=3, backoff_ms=200, jitter_ms=0)
    assert delays == [200, 400, 800]
