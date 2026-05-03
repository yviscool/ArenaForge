import json
import re
import unittest
from pathlib import Path
from typing import Dict, Set

LOCALE_ROOT = Path("arena_forge/locales")
PLACEHOLDER_PATTERN = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def _load_locale(name: str) -> Dict[str, str]:
    return json.loads((LOCALE_ROOT / f"{name}.json").read_text(encoding="utf-8"))


def _extract_placeholders(value: str) -> Set[str]:
    return set(PLACEHOLDER_PATTERN.findall(value))


class LocaleCatalogTests(unittest.TestCase):
    def test_locale_key_sets_match(self) -> None:
        en = _load_locale("en")
        zh = _load_locale("zh-Hans")
        self.assertEqual(set(en), set(zh))

    def test_locale_placeholders_match(self) -> None:
        en = _load_locale("en")
        zh = _load_locale("zh-Hans")
        for key in en:
            self.assertEqual(
                _extract_placeholders(en[key]),
                _extract_placeholders(zh[key]),
                msg=key,
            )


if __name__ == "__main__":
    unittest.main()
