from __future__ import annotations

from .action_handlers import RunPanelActionContext, build_test_manager_action_handlers
from .action_request import RunPanelActionRequest


def dispatch_test_manager_action(
    command,
    edit,
    request: RunPanelActionRequest,
) -> bool:
    context = RunPanelActionContext(command=command, edit=edit, request=request)
    handler = build_test_manager_action_handlers(context).get(request.action)
    if handler is None:
        return True
    handler.callback(context)
    return handler.sync_read_only
