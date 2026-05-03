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

    @classmethod
    def from_command_args(
        cls,
        *,
        action=None,
        run_file=None,
        build_sys=None,
        text=None,
        clr_tests=False,
        sync_out=False,
        code_view_id=None,
        var_name=None,
        use_debugger=False,
        pos=None,
        load_session=False,
        region=None,
        frame_id=None,
        data=None,
        id=None,
        dir=1,
    ) -> "RunPanelActionRequest":
        return cls(
            action=action,
            run_file=run_file,
            build_sys=build_sys,
            text=text,
            clr_tests=clr_tests,
            sync_out=sync_out,
            code_view_id=code_view_id,
            var_name=var_name,
            use_debugger=use_debugger,
            pos=pos,
            load_session=load_session,
            region=region,
            frame_id=frame_id,
            data=data,
            id=id,
            dir=dir,
        )

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
