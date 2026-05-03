import json
import unittest
from pathlib import Path

from arena_forge.adapters.sublime.command_action_catalog import (
    SUPPORTED_TEST_EDITOR_ACTIONS,
    SUPPORTED_TEST_MANAGER_ACTIONS,
)


class CommandSurfaceTests(unittest.TestCase):
    def test_test_manager_action_surface_stays_explicit(self) -> None:
        self.assertIn("make_opd", SUPPORTED_TEST_MANAGER_ACTIONS)
        self.assertIn("toggle_hide_phantoms", SUPPORTED_TEST_MANAGER_ACTIONS)
        self.assertIn("redirect_var_value", SUPPORTED_TEST_MANAGER_ACTIONS)

    def test_test_editor_action_surface_stays_explicit(self) -> None:
        self.assertIn("init", SUPPORTED_TEST_EDITOR_ACTIONS)
        self.assertIn("insert_opd_out", SUPPORTED_TEST_EDITOR_ACTIONS)
        self.assertIn("toggle_using_debugger", SUPPORTED_TEST_EDITOR_ACTIONS)

    def test_default_commands_keep_history_and_credentials_entries(self) -> None:
        payload = json.loads(Path("Default.sublime-commands").read_text(encoding="utf-8"))
        captions = {item["caption"] for item in payload}
        commands = {item["command"] for item in payload}
        self.assertIn("ArenaForge: Configure Credentials / \u914d\u7f6e\u51ed\u636e", captions)
        self.assertIn("ArenaForge: Doctor / \u5065\u5eb7\u68c0\u67e5", captions)
        self.assertIn("ArenaForge: Run History / \u8fd0\u884c\u5386\u53f2", captions)
        self.assertIn("ArenaForge: Open History Source / \u6253\u5f00\u5386\u53f2\u6e90\u6587\u4ef6", captions)
        self.assertIn("ArenaForge: Clear All Tests / \u6e05\u7a7a\u5168\u90e8\u6d4b\u8bd5", captions)
        self.assertIn("arena_forge_open_settings", commands)
        self.assertIn("arena_forge_doctor", commands)
        self.assertIn("arena_forge_run_history", commands)
        self.assertIn("arena_forge_open_history_source", commands)
        self.assertIn("arena_forge_clear_all_tests", commands)

    def test_main_menu_groups_package_settings_under_arenaforge(self) -> None:
        payload = json.loads(Path("Main.sublime-menu").read_text(encoding="utf-8"))
        preferences = next(item for item in payload if item.get("id") == "preferences")
        package_settings = next(item for item in preferences["children"] if item.get("id") == "package-settings")
        arena_forge = next(item for item in package_settings["children"] if item["caption"] == "ArenaForge")

        captions = {item["caption"] for item in arena_forge["children"]}
        self.assertIn("Settings - Default", captions)
        self.assertIn("Settings - User", captions)
        self.assertIn("Commands", captions)

        commands_group = next(item for item in arena_forge["children"] if item["caption"] == "Commands")
        command_ids = {item["command"] for item in commands_group["children"] if "command" in item}
        self.assertIn("arena_forge_open_settings", command_ids)
        self.assertIn("arena_forge_doctor", command_ids)
        self.assertIn("arena_forge_run_history", command_ids)
        self.assertIn("arena_forge_clear_all_tests", command_ids)


if __name__ == "__main__":
    unittest.main()
