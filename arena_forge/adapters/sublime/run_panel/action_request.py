from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from arena_forge.adapters.i18n.catalog import translate_catalog as translate


@dataclass(frozen=True)
class RunPanelActionRequest:
    action: Optional[str] = None
    run_file: Optional[str] = None
    build_sys: Optional[str] = None
    text: Optional[str] = None
    clr_tests: bool = False
    sync_out: bool = False
    code_view_id: Optional[int] = None
    var_name: Optional[str] = None
    use_debugger: bool = False
    pos: Optional[int] = None
    load_session: bool = False
    region: Any = None
    frame_id: Optional[int] = None
    data: Any = None
    id: Optional[int] = None
    dir: int = 1

    _LAUNCH_FIELDS = (
        "run_file", "build_sys", "clr_tests", "sync_out",
        "code_view_id", "use_debugger", "load_session",
    )

    def to_command_args(self) -> Dict[str, Any]:
        return {"action": "make_opd", **{k: getattr(self, k) for k in self._LAUNCH_FIELDS}}

    def to_launch_session(self) -> Any:
        from .controller_state import RunPanelLaunchSession

        if self.run_file is None:
            raise ValueError(translate("error.run_file_required"))
        return RunPanelLaunchSession(
            run_file=self.run_file,
            build_sys=self.build_sys,
            clr_tests=self.clr_tests,
            sync_out=self.sync_out,
            code_view_id=self.code_view_id,
            use_debugger=self.use_debugger,
        )
