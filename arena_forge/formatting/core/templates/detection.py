from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional, Sequence, Set, Tuple

from arena_forge.formatting.core.discovery import iter_ancestor_dirs

from .models import (
    DETECTION_EXTENSIONS,
    DETECTION_MARKERS,
    IGNORED_SCAN_DIRS,
    SUPPORTED_ADAPTER_ORDER,
    VCS_ROOT_MARKERS,
    TargetCandidate,
)


def resolve_workspace_root(
    start_dir: Optional[str],
    window_folders: Sequence[str],
) -> Optional[str]:
    candidates = resolve_target_candidates(start_dir, window_folders)
    if candidates:
        return candidates[0].path
    return None


def resolve_target_candidates(
    start_dir: Optional[str],
    window_folders: Sequence[str],
    *,
    adapter_id: Optional[str] = None,
) -> Tuple[TargetCandidate, ...]:
    resolved_start = Path(start_dir).resolve() if start_dir else None
    resolved_folders = tuple(Path(folder).resolve() for folder in window_folders if folder)

    candidates = []
    seen = set()  # type: Set[str]

    smart_root, smart_reason = detect_smart_project_root(resolved_start, adapter_id=adapter_id)
    if smart_root:
        _append_target_candidate(
            candidates,
            seen,
            TargetCandidate(
                id="smart-project",
                caption="Project Root (Recommended)",
                description=smart_reason,
                path=str(smart_root),
                reason=smart_reason,
            ),
        )

    workspace_root = None
    if resolved_start:
        workspace_root = _deepest_matching_folder(resolved_start, resolved_folders)
    elif resolved_folders:
        workspace_root = resolved_folders[0]
    if workspace_root is not None:
        _append_target_candidate(
            candidates,
            seen,
            TargetCandidate(
                id="workspace-folder",
                caption="Window Folder",
                description="Use the matching top-level folder opened in Sublime Text.",
                path=str(workspace_root),
                reason="Matched an open workspace folder.",
            ),
        )

    if resolved_start is not None:
        _append_target_candidate(
            candidates,
            seen,
            TargetCandidate(
                id="current-directory",
                caption="Current File Directory",
                description="Write config files beside the current file.",
                path=str(resolved_start),
                reason="Uses the active file directory directly.",
            ),
        )

    return tuple(candidates)


def detect_workspace_languages(root_dir: str) -> Tuple[str, ...]:
    found = set()  # type: Set[str]
    all_known = set(DETECTION_MARKERS).union(DETECTION_EXTENSIONS)

    for _current_root, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [name for name in dirnames if name not in IGNORED_SCAN_DIRS]
        _detect_from_filenames(found, filenames)
        if found >= all_known:
            break

    ordered = [adapter_id for adapter_id in SUPPORTED_ADAPTER_ORDER if adapter_id in found]
    return tuple(ordered)


def detect_smart_project_root(
    start_dir: Optional[Path],
    *,
    adapter_id: Optional[str] = None,
) -> Tuple[Optional[Path], str]:
    if start_dir is None:
        return None, "No active file or workspace folder was available."

    for ancestor in iter_ancestor_dirs(str(start_dir)):
        marker = _first_matching_marker(ancestor, adapter_id=adapter_id)
        if marker:
            return ancestor, f"Nearest project marker: {marker}"
        for marker in VCS_ROOT_MARKERS:
            if (ancestor / marker).exists():
                return ancestor, f"Nearest VCS root: {marker}"

    return start_dir, "No project marker was found; using the current directory."


def _append_target_candidate(
    candidates: list,
    seen: Set[str],
    candidate: TargetCandidate,
) -> None:
    normalized = str(Path(candidate.path).resolve())
    if normalized in seen:
        return
    seen.add(normalized)
    candidates.append(candidate)


def _first_matching_marker(path: Path, *, adapter_id: Optional[str]) -> Optional[str]:
    adapter_ids = (adapter_id,) if adapter_id else SUPPORTED_ADAPTER_ORDER
    for current_adapter in adapter_ids:
        if not current_adapter:
            continue
        for marker in DETECTION_MARKERS.get(current_adapter, ()):
            if (path / marker).exists():
                return marker
    return None


def _detect_from_filenames(found: Set[str], filenames: Sequence[str]) -> None:
    for filename in filenames:
        lower_name = filename.lower()
        suffix = Path(lower_name).suffix

        for adapter_id, markers in DETECTION_MARKERS.items():
            if lower_name in markers:
                found.add(adapter_id)

        for adapter_id, extensions in DETECTION_EXTENSIONS.items():
            if suffix in extensions:
                found.add(adapter_id)


def _deepest_matching_folder(start_dir: Path, folders: Iterable[Path]) -> Optional[Path]:
    matches = [folder for folder in folders if _is_relative_to(start_dir, folder)]
    if not matches:
        return None
    return max(matches, key=lambda item: len(item.parts))


def _is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False
