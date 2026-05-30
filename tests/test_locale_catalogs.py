import ast
import json
import re
import unittest
from pathlib import Path
from typing import Dict, Iterable, Set

from arena_forge.product import SUPPORTED_LOCALES

LOCALE_ROOT = Path("arena_forge/locales")
MESSAGE_SOURCE = Path("arena_forge/adapters/sublime/shared/messages.py")
PLACEHOLDER_PATTERN = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def _locale_names() -> Iterable[str]:
    return sorted(path.stem for path in LOCALE_ROOT.glob("*.json"))


def _load_locale(name: str) -> Dict[str, str]:
    return json.loads((LOCALE_ROOT / f"{name}.json").read_text(encoding="utf-8"))


def _load_sublime_fallbacks() -> Dict[str, str]:
    module = ast.parse(MESSAGE_SOURCE.read_text(encoding="utf-8"), filename=str(MESSAGE_SOURCE))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "_FALLBACKS" for target in node.targets):
            continue
        catalog = ast.literal_eval(node.value)
        return {str(key): str(value) for key, value in catalog.items()}
    raise AssertionError("_FALLBACKS not found in shared/messages.py")


def _extract_placeholders(value: str) -> Set[str]:
    return set(PLACEHOLDER_PATTERN.findall(value))


class LocaleCatalogTests(unittest.TestCase):
    def test_supported_locales_match_catalogs(self) -> None:
        self.assertEqual(tuple(_locale_names()), tuple(sorted(SUPPORTED_LOCALES)))

    def test_english_locale_matches_sublime_fallbacks(self) -> None:
        self.assertEqual(_load_locale("en"), _load_sublime_fallbacks())

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
