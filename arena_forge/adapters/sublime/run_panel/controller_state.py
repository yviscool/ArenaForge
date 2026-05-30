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
class RunPanelInputBufferState:
    input_start: int = 0
    delta_input: int = 0

    def begin_at(self, point: int) -> None:
        self.input_start = point
        self.delta_input = point

    def advance_to(self, point: int) -> None:
        self.delta_input = point

    def reset(self) -> None:
        self.begin_at(0)


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
    input_buffer: RunPanelInputBufferState = field(default_factory=RunPanelInputBufferState)
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
        self.input_buffer.begin_at(point)

    def advance_panel_input(self, point: int) -> None:
        self.input_buffer.advance_to(point)

    def reset_panel_runtime(self) -> None:
        self.input_buffer.reset()
        self.history.clear()

    @property
    def delta_input(self) -> int:
        return self.input_buffer.delta_input

    @delta_input.setter
    def delta_input(self, value: int) -> None:
        self.input_buffer.advance_to(value)

    @property
    def input_start(self) -> int:
        return self.input_buffer.input_start

    @input_start.setter
    def input_start(self, value: int) -> None:
        self.input_buffer.input_start = value

    @property
    def dbg_file(self) -> Optional[str]:
        return self.source_file

    @dbg_file.setter
    def dbg_file(self, value: Optional[str]) -> None:
        self.source_file = value

    @property
    def input_history(self) -> List[str]:
        return self.history.entries

    @input_history.setter
    def input_history(self, value: List[str]) -> None:
        self.history.entries = list(value)

    @property
    def history_index(self) -> Optional[int]:
        return self.history.index

    @history_index.setter
    def history_index(self, value: Optional[int]) -> None:
        self.history.index = value

    @property
    def history_draft(self) -> str:
        return self.history.draft

    @history_draft.setter
    def history_draft(self, value: str) -> None:
        self.history.draft = value
