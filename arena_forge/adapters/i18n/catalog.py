from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

_DEFAULT_LOCALE_DIRECTORY = Path(__file__).resolve().parents[2] / "locales"


class JsonCatalogTranslator:
    def __init__(self, locale_directory: str, default_locale: str = "en"):
        self.locale_directory = Path(locale_directory)
        self.default_locale = default_locale
        self._cache: dict[str, dict[str, str]] = {}

    def _load(self, locale: str) -> dict[str, str]:
        if locale not in self._cache:
            path = self.locale_directory / f"{locale}.json"
            try:
                with path.open("r", encoding="utf-8") as handle:
                    self._cache[locale] = json.load(handle)
            except FileNotFoundError:
                if locale != self.default_locale:
                    return self._load(self.default_locale)
                raise
        return self._cache[locale]

    def translate(self, key: str, locale: Optional[str] = None, **kwargs: str) -> str:
        locale = locale or self.default_locale
        catalog = self._load(locale)
        template = catalog.get(key)
        if template is None and locale != self.default_locale:
            template = self._load(self.default_locale).get(key, key)
        elif template is None:
            template = key
        return template.format(**kwargs)


_default_translator = JsonCatalogTranslator(str(_DEFAULT_LOCALE_DIRECTORY), default_locale="en")


def translate_catalog(key: str, locale: Optional[str] = None, **kwargs: str) -> str:
    return _default_translator.translate(key, locale=locale, **kwargs)
