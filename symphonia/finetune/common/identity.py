"""Stable identity helpers for dataset records."""
from __future__ import annotations

import hashlib
import json


def stable_id(rec: dict) -> str:
    """Return a deterministic identifier for *rec*.

    The identifier is the first 16 hex characters of the SHA256 hash over
    the minified JSON representation of the record's ``input`` and
    ``target`` fields with keys sorted. This ensures that identical records
    across runs yield the same id irrespective of key ordering."""

    payload = json.dumps({"input": rec.get("input"), "target": rec.get("target")},
                          sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def bucket(rec_id: str) -> int:
    """Map ``rec_id`` to a deterministic bucket in ``[0, 99]``.

    The implementation uses SHA1 hashing which is sufficient for the small
    datasets used in tests."""

    return int(hashlib.sha1(rec_id.encode("utf-8")).hexdigest(), 16) % 100


def split_for_id(rec_id: str) -> str:
    """Return the dataset split for ``rec_id``.

    The default partitioning uses 90% train, 5% val and 5% test buckets and
    is deterministic across runs."""

    b = bucket(rec_id)
    if b < 90:
        return "train"
    if b < 95:
        return "val"
    return "test"
