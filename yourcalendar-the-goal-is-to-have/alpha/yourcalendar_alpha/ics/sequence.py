from __future__ import annotations

import hashlib


def build_event_sequence(source_hash: str) -> str:
    return str(int(hashlib.sha1(source_hash.encode("utf-8")).hexdigest()[:6], 16))
