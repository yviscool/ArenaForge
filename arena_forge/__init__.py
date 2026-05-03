import sys as _sys

from .product import (
    DISPLAY_NAME,
    SETTINGS_FILE,
    __version__,
)

_sys.modules.setdefault("arena_forge", _sys.modules[__name__])

__all__ = [
    "__version__",
    "DISPLAY_NAME",
    "SETTINGS_FILE",
]
