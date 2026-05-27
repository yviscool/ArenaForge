from __future__ import annotations

from typing import Dict, Optional, Tuple

from arena_forge.formatting.adapters.base import FormatterAdapter
from arena_forge.formatting.adapters.clang import ClangFormatAdapter
from arena_forge.formatting.adapters.go import GoFormatAdapter
from arena_forge.formatting.adapters.java import GoogleJavaFormatAdapter
from arena_forge.formatting.adapters.kotlin import KtfmtAdapter
from arena_forge.formatting.adapters.oxfmt import OxcFormatAdapter
from arena_forge.formatting.adapters.ruff import RuffFormatAdapter
from arena_forge.formatting.adapters.rust import RustFormatAdapter

ADAPTERS = (  # type: Tuple[FormatterAdapter, ...]
    ClangFormatAdapter(),
    GoFormatAdapter(),
    GoogleJavaFormatAdapter(),
    KtfmtAdapter(),
    RuffFormatAdapter(),
    RustFormatAdapter(),
    OxcFormatAdapter(),
)


def adapter_by_id(adapter_id: str) -> Optional[FormatterAdapter]:
    for adapter in ADAPTERS:
        if adapter.id == adapter_id:
            return adapter
    return None


def selectors_for_adapter(
    adapter: FormatterAdapter,
    selector_overrides: Dict[str, Tuple[str, ...]],
) -> Tuple[str, ...]:
    return adapter.selectors + tuple(selector_overrides.get(adapter.id, ()))
