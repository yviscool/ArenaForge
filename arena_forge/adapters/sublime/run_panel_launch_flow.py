from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .run_panel_controller_state import RunPanelLaunchSession


@dataclass(frozen=True)
class RunPanelLaunchRequest:
    run_file: Optional[str] = None
    build_sys: Optional[str] = None
    clr_tests: bool = False
    sync_out: bool = False
    code_view_id: Optional[int] = None
    use_debugger: bool = False
    load_session: bool = False

    def to_command_args(self) -> Dict[str, Any]:
        return {
            "action": "make_opd",
            "run_file": self.run_file,
            "build_sys": self.build_sys,
            "clr_tests": self.clr_tests,
            "sync_out": self.sync_out,
            "code_view_id": self.code_view_id,
            "use_debugger": self.use_debugger,
            "load_session": self.load_session,
        }

    def to_launch_session(self) -> RunPanelLaunchSession:
        if self.run_file is None:
            raise ValueError("run_file is required for a fresh run-panel launch")
        return RunPanelLaunchSession(
            run_file=self.run_file,
            build_sys=self.build_sys,
            clr_tests=self.clr_tests,
            sync_out=self.sync_out,
            code_view_id=self.code_view_id,
            use_debugger=self.use_debugger,
        )


@dataclass(frozen=True)
class RunPanelLaunchPlan:
    action: str
    session: Optional[RunPanelLaunchSession] = None
    command_args: Optional[Dict[str, Any]] = None
    error_key: Optional[str] = None


def plan_run_panel_launch(
    *,
    status_code: Optional[str],
    request: RunPanelLaunchRequest,
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
