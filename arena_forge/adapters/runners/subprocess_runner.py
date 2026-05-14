from __future__ import annotations

import os
import shlex
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import List, Optional

from arena_forge.core.domain import CommandExecution, LanguageProfile, TestRunResult, Verdict


@dataclass
class _StartupInfoProxy:
    dwFlags: int = 0
    wShowWindow: int = 0


def build_command_context(source_file: str, args: str = "") -> dict[str, str]:
    source_path = Path(source_file)
    return {
        "file": source_path.name,
        "source_file": str(source_path),
        "source_file_dir": str(source_path.parent),
        "file_name": source_path.stem,
        "args": args,
    }


def render_command(template: str, source_file: str, args: str = "") -> str:
    return template.format(**build_command_context(source_file, args=args))


def build_command_argv(command: str, platform_name: Optional[str] = None) -> List[str]:
    del platform_name
    return shlex.split(command, posix=True)


def build_process_spawn_options(platform_name: Optional[str] = None) -> dict:
    normalized = (platform_name or os.name).lower()
    if normalized in {"nt", "windows"}:
        startupinfo_cls = getattr(subprocess, "STARTUPINFO", None)
        startupinfo = startupinfo_cls() if startupinfo_cls is not None else _StartupInfoProxy()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
        startupinfo.wShowWindow = 0
        return {
            "startupinfo": startupinfo,
            "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
            "preexec_fn": None,
        }
    return {
        "startupinfo": None,
        "creationflags": 0,
        "preexec_fn": os.setsid,
    }


def _resolve_subprocess_spawn_options(spawn_options: dict) -> dict:
    if hasattr(subprocess, "STARTUPINFO"):
        return spawn_options
    return {
        "startupinfo": None,
        "creationflags": 0,
        "preexec_fn": spawn_options["preexec_fn"],
    }


def build_process_text_options(platform_name: Optional[str] = None) -> dict:
    del platform_name
    return {
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }


def compile_once(
    profile: LanguageProfile,
    source_file: str,
    platform_name: Optional[str] = None,
) -> Optional[CommandExecution]:
    if not profile.compile_cmd:
        return None
    command = render_command(profile.compile_cmd, source_file)
    argv = build_command_argv(command, platform_name=platform_name)
    spawn_options = _resolve_subprocess_spawn_options(build_process_spawn_options(platform_name))
    text_options = build_process_text_options(platform_name)
    started_at = perf_counter()
    completed = subprocess.run(
        argv,
        cwd=str(Path(source_file).resolve().parent),
        capture_output=True,
        check=False,
        startupinfo=spawn_options["startupinfo"],
        creationflags=spawn_options["creationflags"],
        **text_options,
    )
    runtime_ms = int((perf_counter() - started_at) * 1000)
    stdout = (completed.stdout or "") + (completed.stderr or "")
    return CommandExecution(
        argv=tuple(argv),
        return_code=completed.returncode,
        stdout=stdout,
        runtime_ms=runtime_ms,
    )


def run_once(
    profile: LanguageProfile,
    source_file: str,
    input_text: str,
    platform_name: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
) -> TestRunResult:
    if not profile.run_cmd:
        raise ValueError(f"Language profile {profile.name!r} has no run command")

    command = render_command(profile.run_cmd, source_file)
    argv = build_command_argv(command, platform_name=platform_name)
    spawn_options = _resolve_subprocess_spawn_options(build_process_spawn_options(platform_name))
    text_options = build_process_text_options(platform_name)
    started_at = perf_counter()
    try:
        completed = subprocess.run(
            argv,
            cwd=str(Path(source_file).resolve().parent),
            input=input_text,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            startupinfo=spawn_options["startupinfo"],
            creationflags=spawn_options["creationflags"],
            **text_options,
        )
        runtime_ms = int((perf_counter() - started_at) * 1000)
        stdout = (completed.stdout or "") + (completed.stderr or "")
        verdict = Verdict.UNKNOWN if completed.returncode == 0 else Verdict.RUNTIME_ERROR
        return TestRunResult(
            output_text=stdout,
            return_code=completed.returncode,
            runtime_ms=runtime_ms,
            verdict=verdict,
            command=tuple(argv),
        )
    except subprocess.TimeoutExpired as error:
        runtime_ms = int((perf_counter() - started_at) * 1000)
        stdout = (error.stdout or "") + (error.stderr or "")
        return TestRunResult(
            output_text=stdout,
            return_code=-1,
            runtime_ms=runtime_ms,
            verdict=Verdict.TIMEOUT,
            command=tuple(argv),
            message=f"Timed out after {timeout_seconds} seconds",
        )


def build_interactive_process(
    profile: LanguageProfile,
    source_file: str,
    args: Optional[List[str]] = None,
    platform_name: Optional[str] = None,
) -> subprocess.Popen[str]:
    if not profile.run_cmd:
        raise ValueError(f"Language profile {profile.name!r} has no run command")

    merged_args = " ".join(args or ())
    command = render_command(profile.run_cmd, source_file, args=merged_args)
    argv = build_command_argv(command, platform_name=platform_name)
    spawn_options = _resolve_subprocess_spawn_options(build_process_spawn_options(platform_name))
    text_options = build_process_text_options(platform_name)
    return subprocess.Popen(
        argv,
        cwd=str(Path(source_file).resolve().parent),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        startupinfo=spawn_options["startupinfo"],
        creationflags=spawn_options["creationflags"],
        preexec_fn=spawn_options["preexec_fn"],
        **text_options,
    )


def terminate_process(process: subprocess.Popen[str], platform_name: Optional[str] = None) -> None:
    platform_name = (platform_name or os.name).lower()
    if platform_name in {"nt", "windows"}:
        process.kill()
        return
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
