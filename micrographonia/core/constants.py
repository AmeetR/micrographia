"""Shared string constants for runner outputs."""

RUNS_DIR = "runs"
META_FILE = "meta.json"
METRICS_FILE = "metrics.json"
TIMELINE_FILE = "timeline.json"
LOG_FILE = "logs.txt"

# stop reasons
COMPLETED = "completed"
PREFLIGHT_FAILED = "preflight_failed"
RUNTIME_ERROR = "runtime_error"
INVALID_PLAN = "invalid_plan"
PLAN_MISMATCH = "plan_mismatch"
RESUME_NOT_SUPPORTED = "resume_not_supported"
INTERRUPTED = "interrupted"

# timeline statuses
STATUS_OK = "ok"
STATUS_FAILED = "failed"

__all__ = [
    "RUNS_DIR",
    "META_FILE",
    "METRICS_FILE",
    "TIMELINE_FILE",
    "LOG_FILE",
    "COMPLETED",
    "PREFLIGHT_FAILED",
    "RUNTIME_ERROR",
    "INVALID_PLAN",
    "PLAN_MISMATCH",
    "RESUME_NOT_SUPPORTED",
    "INTERRUPTED",
    "STATUS_OK",
    "STATUS_FAILED",
]
