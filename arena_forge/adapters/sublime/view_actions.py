from __future__ import annotations

from sublime import Region


def replace_region(view, edit, region: tuple[int, int], text: str) -> None:
    view.replace(edit, Region(region[0], region[1]), text)


def erase_region(view, edit, region: tuple[int, int]) -> None:
    view.erase(edit, Region(region[0], region[1]))


def replace_all(view, edit, text: str) -> None:
    replace_region(view, edit, (0, view.size()), text)


def set_cursor_to_end(view) -> None:
    view.sel().clear()
    view.sel().add(Region(view.size(), view.size()))
