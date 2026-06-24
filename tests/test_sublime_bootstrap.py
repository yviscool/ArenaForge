import unittest
from pathlib import Path

from arena_forge.adapters.sublime import build_sublime_application


class SublimeBootstrapTests(unittest.TestCase):
    def test_application_bootstrap_wires_major_services(self) -> None:
        app = build_sublime_application(
            {"preferred_locale": "en"},
            platform_name="windows",
            locale_directory=Path("arena_forge/locales"),
        )
        self.assertEqual(app.settings["product_name"], "ArenaForge")
        self.assertGreaterEqual(len(app.profiles), 1)
        self.assertIn("codeforces", app.provider_registry._bindings)
        self.assertIn("atcoder", app.provider_registry._bindings)
        self.assertIn("luogu", app.provider_registry._bindings)
        self.assertIn("acwing", app.provider_registry._bindings)
        self.assertIsNotNone(app.submission_service)
        self.assertIsNotNone(app.credential_store)
        self.assertEqual(app.translator.translate("product.name"), "ArenaForge")


if __name__ == "__main__":
    unittest.main()
