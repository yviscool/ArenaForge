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

    def test_defaults_fill_default_contest_language_and_formatting(self) -> None:
        normalized = normalize_settings({}, "linux")
        self.assertEqual(normalized["default_contest_language"], "cpp")
        self.assertIn("formatting", normalized)
        self.assertEqual(normalized["formatting"]["timeout_ms"], 10000)
        self.assertEqual(normalized["lint_timeout_ms"], 3000)

    def test_negative_lint_timeout_clamps_to_zero(self) -> None:
        normalized = normalize_settings({"lint_timeout_ms": -1}, "linux")
        self.assertEqual(normalized["lint_timeout_ms"], 0)

    def test_formatting_maps_normalize_to_lists(self) -> None:
        normalized = normalize_settings(
            {
                "formatting": {
                    "commands": {"google-java-format": ["java", "-jar", "tools/google-java-format.jar"]},
                    "extra_args": {"ruff": "--line-length"},
                }
            },
            "linux",
        )
        self.assertEqual(
            normalized["formatting"]["commands"]["google-java-format"],
            ["java", "-jar", "tools/google-java-format.jar"],
        )
        self.assertEqual(normalized["formatting"]["extra_args"]["ruff"], ["--line-length"])


if __name__ == "__main__":
    unittest.main()
