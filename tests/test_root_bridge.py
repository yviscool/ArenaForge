import sys
import types
import unittest

from arena_forge.adapters.sublime.root_bridge import (
    get_debugger_info_module,
    get_highlight_function,
    get_template_generator,
    resolve_root_package_name,
)


class RootBridgeTests(unittest.TestCase):
    def test_resolve_root_package_name_supports_plain_python_imports(self) -> None:
        self.assertIsNone(resolve_root_package_name("arena_forge.adapters.sublime.root_bridge"))

    def test_resolve_root_package_name_supports_nested_package_installs(self) -> None:
        self.assertEqual(
            resolve_root_package_name("ArenaForge.arena_forge.adapters.sublime.root_bridge"),
            "ArenaForge",
        )
        self.assertEqual(
            resolve_root_package_name("arena_forge.arena_forge.adapters.sublime.root_bridge"),
            "arena_forge",
        )

    def test_plain_python_mode_can_import_root_resource_modules(self) -> None:
        sys.modules.setdefault("sublime", types.SimpleNamespace())
        self.assertTrue(callable(get_highlight_function()))
        self.assertTrue(callable(get_template_generator()))
        debugger_info = get_debugger_info_module()
        self.assertTrue(hasattr(debugger_info, "get_debug_modules"))


if __name__ == "__main__":
    unittest.main()
