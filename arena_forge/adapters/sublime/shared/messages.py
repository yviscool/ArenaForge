from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import sublime

from arena_forge.product import DISPLAY_NAME, SUPPORTED_LOCALES

_LOCALE_DIRECTORY = Path(__file__).resolve().parents[3] / "locales"

_STATUS_KEY_BY_CODE = {
    "COMPILED": "status.compiled",
    "COMPILING": "status.compiling",
    "RUNNING": "status.running",
    "STOPPED": "status.stopped",
}

_VERDICT_KEY_BY_VALUE = {
    "accepted": "verdict.accepted",
    "rejected": "verdict.rejected",
    "unknown": "verdict.unknown",
    "compile_error": "verdict.compile_error",
    "runtime_error": "verdict.runtime_error",
    "timeout": "verdict.timeout",
}


def _normalized_locale(locale: Optional[str]) -> str:
    if locale and locale in SUPPORTED_LOCALES:
        return locale
    return None


def _translator():
    try:
        from .settings_bridge import get_application

        return get_application().translator
    except Exception:
        from arena_forge.adapters.i18n import JsonCatalogTranslator

        return JsonCatalogTranslator(str(_LOCALE_DIRECTORY), default_locale="en")


def translate(key: str, locale: Optional[str] = None, **kwargs: Any) -> str:
    normalized = {name: str(value) for name, value in kwargs.items()}
    return _translator().translate(key, locale=_normalized_locale(locale), **normalized)


def status_message(key: str, **kwargs: Any) -> None:
    sublime.status_message(translate(key, **kwargs))


def product_status_message(key: str, **kwargs: Any) -> None:
    sublime.status_message(f"{DISPLAY_NAME}: {translate(key, **kwargs)}")


def product_log_message(key: str, **kwargs: Any) -> None:
    print(f"{DISPLAY_NAME}: {translate(key, **kwargs)}")


def error_message(key: str, **kwargs: Any) -> None:
    sublime.error_message(translate(key, **kwargs))


def product_error_message(key: str, **kwargs: Any) -> None:
    sublime.error_message(f"{DISPLAY_NAME}: {translate(key, **kwargs)}")


def translate_verdict(verdict: Any) -> str:
    normalized = getattr(verdict, "value", verdict)
    verdict_key = _VERDICT_KEY_BY_VALUE.get(str(normalized))
    if verdict_key is None:
        return str(normalized)
    return translate(verdict_key)


def translate_status_code(status_code: str) -> str:
    return translate(_STATUS_KEY_BY_CODE.get(status_code, status_code))
