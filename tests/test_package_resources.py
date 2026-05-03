import unittest

from arena_forge.adapters.sublime.package_resources import (
    ARROW_LEFT_ICON_RESOURCE,
    ARROW_RIGHT_ICON_RESOURCE,
    STRESS_SYNTAX_RESOURCE,
    TEST_SYNTAX_RESOURCE,
    build_package_resource_path,
    get_plugin_package_name,
)


class PackageResourcesTests(unittest.TestCase):
    def test_build_package_resource_path_uses_detected_package_name(self) -> None:
        expected = "Packages/{}/TestSyntax.sublime-syntax".format(get_plugin_package_name())
        self.assertEqual(TEST_SYNTAX_RESOURCE, expected)

    def test_build_package_resource_path_normalizes_segments(self) -> None:
        resource_path = build_package_resource_path("icons\\arrow_right.png")
        self.assertEqual(resource_path, ARROW_RIGHT_ICON_RESOURCE)
        self.assertEqual(ARROW_LEFT_ICON_RESOURCE.count("/"), 3)

    def test_known_resource_constants_match_expected_suffixes(self) -> None:
        self.assertTrue(STRESS_SYNTAX_RESOURCE.endswith("/StressSyntax.sublime-syntax"))
        self.assertTrue(TEST_SYNTAX_RESOURCE.endswith("/TestSyntax.sublime-syntax"))
        self.assertTrue(ARROW_RIGHT_ICON_RESOURCE.endswith("/icons/arrow_right.png"))


if __name__ == "__main__":
    unittest.main()
