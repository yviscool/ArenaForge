from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "ArenaForgeAutoCommand",
    "ArenaForgeClearAllTestsCommand",
    "ArenaForgeConfigureCredentialsCommand",
    "ArenaForgeDoctorCommand",
    "ArenaForgeMakeStressCommand",
    "ArenaForgeOpenHistorySourceCommand",
    "ArenaForgeOpenSettingsCommand",
    "ArenaForgeRunCommand",
    "ArenaForgeRunHistoryCommand",
    "ArenaForgeSelectFrameCommand",
    "ArenaForgeSetupContestCommand",
    "ArenaForgeStopStressCommand",
    "ArenaForgeSubmitCommand",
    "HISTORY_SOURCE_FILE_KEY",
    "RunHistoryOpenSourceCommand",
    "RunHistoryPanelCommand",
    "build_history_report",
]

_EXPORT_MODULES = {
    "ArenaForgeAutoCommand": ".window_commands",
    "ArenaForgeClearAllTestsCommand": ".window_commands",
    "ArenaForgeConfigureCredentialsCommand": ".window_commands",
    "ArenaForgeDoctorCommand": ".window_commands",
    "ArenaForgeMakeStressCommand": ".window_commands",
    "ArenaForgeOpenHistorySourceCommand": ".window_commands",
    "ArenaForgeOpenSettingsCommand": ".window_commands",
    "ArenaForgeRunCommand": ".window_commands",
    "ArenaForgeRunHistoryCommand": ".window_commands",
    "ArenaForgeSelectFrameCommand": ".window_commands",
    "ArenaForgeSetupContestCommand": ".window_commands",
    "ArenaForgeStopStressCommand": ".window_commands",
    "ArenaForgeSubmitCommand": ".window_commands",
    "HISTORY_SOURCE_FILE_KEY": ".history_commands",
    "RunHistoryOpenSourceCommand": ".history_commands",
    "RunHistoryPanelCommand": ".history_commands",
    "build_history_report": ".history_commands",
}


def __getattr__(name: str) -> Any:
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    return getattr(module, name)
