from __future__ import annotations

from typing import Any

__all__ = ["SublimeApplication", "build_sublime_application"]


def __getattr__(name: str) -> Any:
    if name in {"SublimeApplication", "build_sublime_application"}:
        from .bootstrap import SublimeApplication, build_sublime_application

        exports = {
            "SublimeApplication": SublimeApplication,
            "build_sublime_application": build_sublime_application,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
