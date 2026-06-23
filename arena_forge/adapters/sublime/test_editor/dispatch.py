from __future__ import annotations

from ..view_actions import replace_region


def dispatch_test_editor_action(
    command,
    edit,
    *,
    action=None,
    text=None,
    test="",
    source_view_id=None,
    test_id=None,
    region=None,
) -> None:
    action_handlers = {
        "init": lambda: command.init(
            edit,
            test=test,
            source_view_id=source_view_id,
            test_id=test_id,
        ),
        "replace": lambda: replace_region(command.view, edit, region, text),
    }
    handler = action_handlers.get(action)
    if handler is None:
        return
    handler()
