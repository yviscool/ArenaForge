from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sublime import PhantomSet


@dataclass
class RunPanelControllerState:
    use_debugger: bool = False
    delta_input: int = 0
    tester: Optional[object] = None
    session: Optional[dict] = None
    input_start: int = 0
    output_start: int = 0
    out_region_set: bool = False
    dbg_file: Optional[str] = None
    code_view_id: Optional[int] = None
    text_buffer: str = ""
    sel_buffer: Optional[object] = None
    phantoms: Optional[PhantomSet] = None
    test_phantoms: list[PhantomSet] = field(default_factory=list)
    input_history: List[str] = field(default_factory=list)
    history_index: Optional[int] = None
    history_draft: str = ""
