from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, cast

Translator = Callable[..., str]

_DOCTOR_FALLBACKS = {
    "doctor.title": "ArenaForge Doctor",
    "doctor.package_name": "Package name",
    "doctor.package_root": "Package root",
    "doctor.resource_root": "Resource root",
    "doctor.contests_root": "Contests root",
    "doctor.credential_backend": "Credential backend",
    "doctor.available": "available",
    "doctor.unavailable": "unavailable",
    "doctor.checks": "Checks",
    "doctor.run_profiles": "Run profiles",
    "doctor.lint_profiles": "Lint profiles",
    "doctor.formatting": "Formatting",
    "doctor.formatter_commands": "{count} formatter command overrides",
    "doctor.required_file": "Required file {name}",
    "doctor.resource": "Resource {name}",
    "doctor.configured": "{count} configured",
    "doctor.profiles_with_lint_compile": "{count} profiles with lint compile commands",
    "doctor.not_found": "not found",
    "doctor.status.ok": "OK",
    "doctor.status.warn": "WARN",
}


def _translate(translate_text: Optional[Translator], key: str, **kwargs: Any) -> str:
    if translate_text is not None:
        return translate_text(key, **kwargs)
    template = _DOCTOR_FALLBACKS.get(key, key)
    normalized = {name: str(value) for name, value in kwargs.items()}
    return template.format(**normalized)


def _format_check(ok: bool, label: str, detail: str, *, translate_text: Optional[Translator]) -> str:
    status = _translate(translate_text, "doctor.status.ok" if ok else "doctor.status.warn")
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
    translate_text: Optional[Translator] = None,
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
    formatting = cast(Mapping[str, object], settings.get("formatting") or {})
    formatter_commands = cast(Mapping[str, object], formatting.get("commands") or {})
    title = _translate(translate_text, "doctor.title")
    checks_title = _translate(translate_text, "doctor.checks")
    availability = _translate(
        translate_text,
        "doctor.available" if credential_available else "doctor.unavailable",
    )

    lines = [
        title,
        "=" * len(title),
        "",
        f"{_translate(translate_text, 'doctor.package_name')}: {package_name}",
        f"{_translate(translate_text, 'doctor.package_root')}: {package_root}",
        f"{_translate(translate_text, 'doctor.resource_root')}: {package_resource_root}",
        f"{_translate(translate_text, 'doctor.contests_root')}: {contests_root}",
        f"{_translate(translate_text, 'doctor.credential_backend')}: {credential_backend} ({availability})",
        "",
        checks_title,
        "-" * len(checks_title),
        _format_check(
            bool(run_settings),
            _translate(translate_text, "doctor.run_profiles"),
            _translate(translate_text, "doctor.configured", count=len(run_settings)),
            translate_text=translate_text,
        ),
        _format_check(
            bool(lint_profiles),
            _translate(translate_text, "doctor.lint_profiles"),
            _translate(translate_text, "doctor.profiles_with_lint_compile", count=len(lint_profiles)),
            translate_text=translate_text,
        ),
        _format_check(
            bool(formatting),
            _translate(translate_text, "doctor.formatting"),
            _translate(translate_text, "doctor.formatter_commands", count=len(formatter_commands)),
            translate_text=translate_text,
        ),
    ]
    lines.extend(
        _format_check(
            exists,
            _translate(translate_text, "doctor.required_file", name=name),
            str(package_root / name),
            translate_text=translate_text,
        )
        for name, exists in existing_files.items()
    )
    for resource_name, matches in discovered_resources.items():
        lines.append(
            _format_check(
                bool(matches),
                _translate(translate_text, "doctor.resource", name=resource_name),
                ", ".join(matches) if matches else _translate(translate_text, "doctor.not_found"),
                translate_text=translate_text,
            )
        )
    return "\n".join(lines) + "\n"
