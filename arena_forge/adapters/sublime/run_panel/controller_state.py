from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(frozen=True)
class RunPanelLaunchSession:
    run_file: str
    build_sys: Optional[str]
    clr_tests: bool
    sync_out: bool
    code_view_id: Optional[int]
    use_debugger: bool


@dataclass
class RunPanelInputHistoryState:
    entries: List[str] = field(default_factory=list)
    index: Optional[int] = None
    draft: str = ""

    def reset_navigation(self) -> None:
        self.index = None
        self.draft = ""

    def push(self, text: str) -> None:
        if not text:
            return
        if self.entries and self.entries[-1] == text:
            self.reset_navigation()
            return
        self.entries.append(text)
        self.reset_navigation()

    def clear(self) -> None:
        self.entries.clear()
        self.reset_navigation()


@dataclass
class RunPanelControllerState:
    use_debugger: bool = False
    tester: Optional[object] = None
    launch_session: Optional[RunPanelLaunchSession] = None
    input_start: int = 0
    delta_input: int = 0
    source_file: Optional[str] = None
    code_view_id: Optional[int] = None
    text_buffer: str = ""
    sel_buffer: Optional[object] = None
    phantoms: Optional[Any] = None
    test_phantoms: list[Any] = field(default_factory=list)
    history: RunPanelInputHistoryState = field(default_factory=RunPanelInputHistoryState)

    def remember_launch(
        self,
        *,
        run_file: str,
        build_sys: Optional[str],
        clr_tests: bool,
        sync_out: bool,
        code_view_id: Optional[int],
        use_debugger: bool,
    ) -> RunPanelLaunchSession:
        launch_session = RunPanelLaunchSession(
            run_file=run_file,
            build_sys=build_sys,
            clr_tests=clr_tests,
            sync_out=sync_out,
            code_view_id=code_view_id,
            use_debugger=use_debugger,
        )
        return self.set_launch_session(launch_session)

    def set_launch_session(self, launch_session: RunPanelLaunchSession) -> RunPanelLaunchSession:
        self.launch_session = launch_session
        self.use_debugger = launch_session.use_debugger
        self.source_file = launch_session.run_file
        self.code_view_id = launch_session.code_view_id
        return launch_session

    def restore_launch(self) -> Optional[RunPanelLaunchSession]:
        if self.launch_session is None:
            return None
        return self.set_launch_session(self.launch_session)

    def begin_panel_input(self, point: int) -> None:
        self.input_start = point
        self.delta_input = point

    def advance_panel_input(self, point: int) -> None:
        self.delta_input = point

    def reset_panel_runtime(self) -> None:
        self.begin_panel_input(0)
        self.history.clear()
