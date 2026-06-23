from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


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

    def to_make_opd_kwargs(self) -> Dict[str, Any]:
        return {
            "run_file": self.run_file,
            "build_sys": self.build_sys,
            "clr_tests": self.clr_tests,
            "sync_out": self.sync_out,
            "code_view_id": self.code_view_id,
            "use_debugger": self.use_debugger,
            "load_session": self.load_session,
        }
