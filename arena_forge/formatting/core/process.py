from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from arena_forge.adapters.i18n.catalog import translate_catalog as translate
from arena_forge.adapters.runners.subprocess_runner import SubprocessExecution, execute_subprocess

TIMEOUT_RETURN_CODE = -2
SYSTEM_ERROR_RETURN_CODE = -1


@dataclass(frozen=True)
class ProcessResult(SubprocessExecution):
    system_error: Optional[str] = None

    @property
    def elapsed_ms(self) -> int:
        return self.runtime_ms


def run_subprocess(
    command: Tuple[str, ...], text: str, cwd: Optional[str], timeout_ms: int
) -> ProcessResult:
    try:
        result = execute_subprocess(
            command,
            cwd=cwd or ".",
            input_text=text,
            timeout_ms=timeout_ms,
        )
    except OSError as exc:
        message = translate(
            "error.formatter_system_error",
            error_type=exc.__class__.__name__,
            detail=str(exc),
        )
        return ProcessResult(
            argv=command,
            returncode=SYSTEM_ERROR_RETURN_CODE,
            stdout="",
            stderr=message,
            runtime_ms=0,
            system_error=message,
        )

    if result.timed_out:
        message = translate("error.formatter_timed_out", timeout_ms=timeout_ms)
        stderr = result.stderr.strip()
        stderr = f"{message}\n\n{stderr}" if stderr else message
        return ProcessResult(
            argv=result.argv,
            returncode=TIMEOUT_RETURN_CODE,
            stdout=result.stdout,
            stderr=stderr,
            runtime_ms=result.runtime_ms,
            timed_out=True,
        )

    return ProcessResult(
        argv=result.argv,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        runtime_ms=result.runtime_ms,
    )
