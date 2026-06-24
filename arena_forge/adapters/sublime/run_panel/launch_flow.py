from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .controller_state import RunPanelLaunchSession


@dataclass(frozen=True)
class RunPanelLaunchPlan:
    action: str
    session: Optional[RunPanelLaunchSession] = None
    command_args: Optional[Dict[str, Any]] = None
    error_key: Optional[str] = None


def plan_run_panel_launch(
    *,
    status_code: Optional[str],
    request,
    saved_session: Optional[RunPanelLaunchSession],
) -> RunPanelLaunchPlan:
    normalized_status = status_code or ""
    if normalized_status == "COMPILING":
        return RunPanelLaunchPlan(action="noop")
    if normalized_status == "RUNNING":
        return RunPanelLaunchPlan(action="rerun", command_args=request.to_command_args())
    if request.load_session:
        if saved_session is None:
            return RunPanelLaunchPlan(action="error", error_key="error.session_restore_failed")
        return RunPanelLaunchPlan(action="launch", session=saved_session)
    return RunPanelLaunchPlan(action="launch", session=request.to_launch_session())
