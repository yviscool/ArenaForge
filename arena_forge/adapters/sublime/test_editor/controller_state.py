from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sublime import PhantomSet


@dataclass
class TestEditorControllerState:
    delta_input: int = 0
    use_debugger: bool = False
    tester: Optional[object] = None
    session: Optional[dict] = None
    test_id: Optional[int] = None
    source_view_id: Optional[int] = None
    phantoms: Optional[PhantomSet] = None
