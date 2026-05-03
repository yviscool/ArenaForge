import unittest

from arena_forge.adapters.sublime.package_resources import (
    ARROW_LEFT_ICON_RESOURCE,
    ARROW_RIGHT_ICON_RESOURCE,
    PackageLayout,
    STRESS_SYNTAX_RESOURCE,
    TEST_SYNTAX_RESOURCE,
    build_package_resource_path,
    get_plugin_package_name,
    get_plugin_root_dir,
    remap_package_syntax_resource,
    resolve_package_layout,
)


class PackageResourcesTests(unittest.TestCase):
    def test_resolve_package_layout_for_repo_root_mount(self) -> None:
        layout = resolve_package_layout("ArenaForge.arena_forge.adapters.sublime.package_resources")
        self.assertEqual(layout, PackageLayout(package_name="ArenaForge", resource_subpath=()))

    def test_resolve_package_layout_for_outer_workspace_mount(self) -> None:
        layout = resolve_package_layout("ArenaForge.arena_forge.arena_forge.adapters.sublime.package_resources")
        self.assertEqual(layout, PackageLayout(package_name="ArenaForge", resource_subpath=("arena_forge",)))

    def test_resolve_package_layout_for_plain_python_import(self) -> None:
        layout = resolve_package_layout("arena_forge.adapters.sublime.package_resources")
        self.assertEqual(layout, PackageLayout(package_name="arena_forge", resource_subpath=()))

    def test_build_package_resource_path_normalizes_segments(self) -> None:
        resource_path = build_package_resource_path("icons\\arrow_right.png")
        self.assertEqual(resource_path, ARROW_RIGHT_ICON_RESOURCE)
        self.assertTrue(ARROW_LEFT_ICON_RESOURCE.endswith("/icons/arrow_left.png"))

    def test_known_resource_constants_match_expected_suffixes(self) -> None:
        self.assertTrue(STRESS_SYNTAX_RESOURCE.endswith("/StressSyntax.sublime-syntax"))
        self.assertTrue(TEST_SYNTAX_RESOURCE.endswith("/TestSyntax.sublime-syntax"))
        self.assertTrue(ARROW_RIGHT_ICON_RESOURCE.endswith("/icons/arrow_right.png"))
        self.assertEqual(get_plugin_package_name(), "arena_forge")

    def test_repo_root_resolution_finds_project_root(self) -> None:
        root_dir = get_plugin_root_dir()
        self.assertTrue((root_dir / "pyproject.toml").exists())
        self.assertTrue((root_dir / "TestSyntax.sublime-syntax").exists())

    def test_remap_package_syntax_resource_repairs_outdated_test_syntax_path(self) -> None:
        self.assertEqual(
            remap_package_syntax_resource("Packages/arena_forge/arena_forge/TestSyntax.sublime-syntax"),
            TEST_SYNTAX_RESOURCE,
        )

    def test_remap_package_syntax_resource_repairs_outdated_stress_syntax_path(self) -> None:
        self.assertEqual(
            remap_package_syntax_resource("Packages/arena_forge/arena_forge/StressSyntax.sublime-syntax"),
            STRESS_SYNTAX_RESOURCE,
        )

    def test_remap_package_syntax_resource_ignores_other_packages(self) -> None:
        self.assertIsNone(remap_package_syntax_resource("Packages/Other/TestSyntax.sublime-syntax"))


if __name__ == "__main__":
    unittest.main()
