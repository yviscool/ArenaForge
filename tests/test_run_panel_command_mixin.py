import importlib
import sys
import types
import unittest
from contextlib import contextmanager


@contextmanager
def _patched_command_mixin_dependencies():
    module_names = (
        "arena_forge.adapters.sublime.shared.messages",
        "arena_forge.adapters.sublime.run_panel.action_request",
        "arena_forge.adapters.sublime.run_panel.command_support",
        "arena_forge.adapters.sublime.run_panel.debug_actions",
        "arena_forge.adapters.sublime.run_panel.dispatch",
        "arena_forge.adapters.sublime.run_panel.display_actions",
        "arena_forge.adapters.sublime.run_panel.edit_actions",
        "arena_forge.adapters.sublime.run_panel.logic",
        "arena_forge.adapters.sublime.run_panel.regions",
        "arena_forge.adapters.sublime.run_panel.session_actions",
        "arena_forge.adapters.sublime.run_panel.test_actions",
        "arena_forge.adapters.sublime.run_panel.command_mixin",
    )
    originals = {name: sys.modules.get(name) for name in module_names}

    class _Request:
        @classmethod
        def from_command_args(cls, **kwargs):
            return {"request": kwargs}

    sys.modules["arena_forge.adapters.sublime.shared.messages"] = types.SimpleNamespace(
        status_message=lambda *args, **kwargs: None
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.action_request"] = types.SimpleNamespace(
        RunPanelActionRequest=_Request
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.command_support"] = types.SimpleNamespace(
        add_transient_region=lambda *args, **kwargs: None,
        change_process_status=lambda *args, **kwargs: None,
        get_style_test_status=lambda *args, **kwargs: None,
        insert_clipboard_input=lambda *args, **kwargs: None,
        insert_panel_input=lambda *args, **kwargs: None,
        memorize_tests=lambda *args, **kwargs: None,
        renumerate_tests=lambda *args, **kwargs: None,
        set_compile_bar=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.debug_actions"] = types.SimpleNamespace(
        get_view_by_id=lambda *args, **kwargs: None,
        prepare_code_view=lambda *args, **kwargs: None,
        redirect_frames=lambda *args, **kwargs: None,
        redirect_var_value=lambda *args, **kwargs: None,
        select_frame=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.dispatch"] = types.SimpleNamespace(
        dispatch_test_manager_action=lambda *args, **kwargs: False
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.display_actions"] = types.SimpleNamespace(
        start_new_test=lambda *args, **kwargs: None,
        update_configs=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.edit_actions"] = types.SimpleNamespace(
        apply_edit_changes=lambda *args, **kwargs: None,
        enable_edit_mode=lambda *args, **kwargs: None,
        get_begin_region=lambda *args, **kwargs: [],
        toggle_new_test=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.logic"] = types.SimpleNamespace(
        should_block_test_action=lambda *args, **kwargs: False
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.regions"] = types.SimpleNamespace(
        compute_tie_pos=lambda *args, **kwargs: 0,
        sync_read_only_mode=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.session_actions"] = types.SimpleNamespace(
        clear_all=lambda *args, **kwargs: None,
        handle_process_stop=lambda *args, **kwargs: None,
        make_opd=lambda *args, **kwargs: None,
    )
    sys.modules["arena_forge.adapters.sublime.run_panel.test_actions"] = types.SimpleNamespace(
        clear_all_tests=lambda *args, **kwargs: None,
        delete_nth_test=lambda *args, **kwargs: None,
        delete_test=lambda *args, **kwargs: None,
        delete_tests=lambda *args, **kwargs: None,
        fold_accept_tests=lambda *args, **kwargs: None,
        handle_accdec_event=lambda *args, **kwargs: None,
        handle_test_event=lambda *args, **kwargs: None,
        open_test_edit=lambda *args, **kwargs: None,
        set_test_input=lambda *args, **kwargs: None,
        set_test_status=lambda *args, **kwargs: None,
        set_tests_status=lambda *args, **kwargs: None,
        swap_tests=lambda *args, **kwargs: None,
        toggle_fold=lambda *args, **kwargs: None,
        toggle_hide_phantoms=lambda *args, **kwargs: None,
    )
    sys.modules.pop("arena_forge.adapters.sublime.run_panel.command_mixin", None)
    try:
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


class RunPanelCommandMixinTests(unittest.TestCase):
    def test_on_test_action_blocks_while_process_is_running(self) -> None:
        with _patched_command_mixin_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_mixin")
            messages = []
            handled = []
            module.status_message = lambda key, **kwargs: messages.append((key, kwargs))
            module.should_block_test_action = lambda proc_run, event: True
            module.handle_run_panel_test_event = lambda *args: handled.append(args)
            command = module.RunPanelCommandMixin()
            command.state = types.SimpleNamespace(tester=types.SimpleNamespace(proc_run=True))

            command.on_test_action(2, "test-run")

            self.assertEqual(messages, [("status.action_while_running", {"action": "test-run"})])
            self.assertEqual(handled, [])

    def test_on_test_action_delegates_when_action_is_allowed(self) -> None:
        with _patched_command_mixin_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_mixin")
            handled = []
            module.should_block_test_action = lambda proc_run, event: False
            module.handle_run_panel_test_event = lambda *args: handled.append(args)
            command = module.RunPanelCommandMixin()
            command.state = types.SimpleNamespace(tester=types.SimpleNamespace(proc_run=False))

            command.on_test_action(1, "test-edit")

            self.assertEqual(handled, [(command, 1, "test-edit")])

    def test_run_syncs_read_only_only_when_dispatch_requests_it(self) -> None:
        with _patched_command_mixin_dependencies():
            module = importlib.import_module("arena_forge.adapters.sublime.run_panel.command_mixin")
            request_args = []

            class _Request:
                @classmethod
                def from_command_args(cls, **kwargs):
                    request_args.append(kwargs)
                    return "REQUEST"

            dispatch_calls = []
            module.RunPanelActionRequest = _Request
            module.dispatch_test_manager_action = lambda command, edit, request: (
                dispatch_calls.append((command, edit, request)) or True
            )
            read_only = []
            syncs = []

            class _Command(module.RunPanelCommandMixin):
                pass

            command = _Command()
            command.view = types.SimpleNamespace(set_read_only=lambda value: read_only.append(value))
            command.sync_read_only = lambda: syncs.append("sync")

            command.run(edit="EDIT", action="insert_line", text="hello", dir=3)

            self.assertEqual(read_only, [False])
            self.assertEqual(syncs, ["sync"])
            self.assertEqual(dispatch_calls, [(command, "EDIT", "REQUEST")])
            self.assertEqual(request_args[0]["action"], "insert_line")
            self.assertEqual(request_args[0]["text"], "hello")
            self.assertEqual(request_args[0]["dir"], 3)


if __name__ == "__main__":
    unittest.main()
