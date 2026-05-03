from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence, cast


def _format_check(ok: bool, label: str, detail: str) -> str:
    status = "OK" if ok else "WARN"
    return f"- [{status}] {label}: {detail}"


def build_doctor_report(
    *,
    package_name: str,
    package_root: Path,
    package_resource_root: str,
    discovered_resources: Mapping[str, Sequence[str]],
    settings: Mapping[str, object],
    contests_root: str,
    credential_backend: str,
    credential_available: bool,
) -> str:
    required_files = (
        "README.md",
        "Main.sublime-menu",
        "Default.sublime-commands",
        "TestSyntax.sublime-syntax",
        "StressSyntax.sublime-syntax",
    )
    existing_files = {name: (package_root / name).exists() for name in required_files}
    run_settings = cast(Sequence[Mapping[str, object]], settings.get("run_settings") or ())
    lint_profiles = [
        profile for profile in run_settings if isinstance(profile, dict) and profile.get("lint_compile_cmd")
    ]

    lines = [
        "ArenaForge Doctor",
        "=================",
        "",
        f"Package name: {package_name}",
        f"Package root: {package_root}",
        f"Resource root: {package_resource_root}",
        f"Contests root: {contests_root}",
        f"Credential backend: {credential_backend} ({'available' if credential_available else 'unavailable'})",
        "",
        "Checks",
        "------",
        _format_check(bool(run_settings), "Run profiles", f"{len(run_settings)} configured"),
        _format_check(
            bool(lint_profiles),
            "Lint profiles",
            f"{len(lint_profiles)} profiles with lint compile commands",
        ),
    ]
    lines.extend(
        _format_check(exists, f"Required file {name}", str(package_root / name))
        for name, exists in existing_files.items()
    )
    for resource_name, matches in discovered_resources.items():
        lines.append(
            _format_check(bool(matches), f"Resource {resource_name}", ", ".join(matches) if matches else "not found")
        )
    return "\n".join(lines) + "\n"
