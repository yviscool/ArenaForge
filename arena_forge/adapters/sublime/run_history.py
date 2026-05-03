from __future__ import annotations

from arena_forge.core.domain import Verdict


def coerce_verdict(value):
    if isinstance(value, Verdict):
        return value
    if value is True:
        return Verdict.ACCEPTED
    if value is False:
        return Verdict.REJECTED
    return Verdict.UNKNOWN
