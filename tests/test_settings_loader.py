import unittest

from arena_forge.adapters.settings_loader import normalize_settings


class SettingsLoaderTests(unittest.TestCase):
    def test_defaults_fill_empty_tests_directory(self) -> None:
        normalized = normalize_settings({"tests_relative_dir": ""}, "linux")
        self.assertEqual(normalized["tests_relative_dir"], ".arena-forge/tests")

    def test_defaults_fill_session_directory(self) -> None:
        normalized = normalize_settings({}, "linux")
        self.assertEqual(normalized["session_relative_dir"], ".arena-forge/sessions")

    def test_invalid_preferred_locale_falls_back_to_default(self) -> None:
        normalized = normalize_settings({"preferred_locale": "fr", "supported_locales": ["en", "zh-Hans"]}, "linux")
        self.assertEqual(normalized["preferred_locale"], "en")

    def test_defaults_fill_ui_and_credential_settings(self) -> None:
        normalized = normalize_settings({}, "linux")
        self.assertEqual(normalized["credential_backend"], "keyring")
        self.assertEqual(normalized["ui_variant"], "terminal")
        self.assertEqual(normalized["ui_density"], "compact")


if __name__ == "__main__":
    unittest.main()
