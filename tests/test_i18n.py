import importlib
import sys
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


class LazyCatalogTests(unittest.TestCase):
    def test_translate_catalog_does_not_eagerly_instantiate_translator(self) -> None:
        mod_name = "arena_forge.adapters.i18n.catalog"
        old_mod = sys.modules.pop(mod_name, None)
        try:
            mod = importlib.import_module(mod_name)
            self.assertIsNone(
                mod._translator_instance,
                "translator should not be instantiated at import time",
            )

            result = mod.translate_catalog("status.settings_loaded")
            self.assertIsInstance(result, str)
            self.assertIsNotNone(mod._translator_instance)

            second = mod.translate_catalog("status.settings_loaded")
            self.assertEqual(result, second)
        finally:
            if old_mod is not None:
                sys.modules[mod_name] = old_mod
            else:
                sys.modules.pop(mod_name, None)


if __name__ == "__main__":
    unittest.main()
