import unittest

from arena_forge.adapters.i18n.catalog import JsonCatalogTranslator
from tests.helpers import local_test_workspace


class I18nTests(unittest.TestCase):
    def test_catalog_falls_back_to_default_locale(self) -> None:
        with local_test_workspace("i18n") as root:
            (root / "en.json").write_text('{"hello": "Hello {name}"}', encoding="utf-8")
            (root / "zh-Hans.json").write_text("{}", encoding="utf-8")
            translator = JsonCatalogTranslator(str(root), default_locale="en")
            self.assertEqual(translator.translate("hello", locale="zh-Hans", name="Coder"), "Hello Coder")


if __name__ == "__main__":
    unittest.main()
