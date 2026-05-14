import json
import re
import unittest
from pathlib import Path
from typing import Dict, Iterable, Set

from arena_forge.product import SUPPORTED_LOCALES

LOCALE_ROOT = Path("arena_forge/locales")
PLACEHOLDER_PATTERN = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def _locale_names() -> Iterable[str]:
    return sorted(path.stem for path in LOCALE_ROOT.glob("*.json"))


def _load_locale(name: str) -> Dict[str, str]:
    return json.loads((LOCALE_ROOT / f"{name}.json").read_text(encoding="utf-8"))


def _extract_placeholders(value: str) -> Set[str]:
    return set(PLACEHOLDER_PATTERN.findall(value))


class LocaleCatalogTests(unittest.TestCase):
    def test_supported_locales_match_catalogs(self) -> None:
        self.assertEqual(tuple(_locale_names()), tuple(sorted(SUPPORTED_LOCALES)))

    def test_locale_key_sets_match(self) -> None:
        en = _load_locale("en")
        for locale_name in _locale_names():
            self.assertEqual(set(en), set(_load_locale(locale_name)), msg=locale_name)

    def test_locale_placeholders_match(self) -> None:
        en = _load_locale("en")
        for locale_name in _locale_names():
            locale = _load_locale(locale_name)
            for key in en:
                self.assertEqual(
                    _extract_placeholders(en[key]),
                    _extract_placeholders(locale[key]),
                    msg=f"{locale_name}:{key}",
                )


if __name__ == "__main__":
    unittest.main()
