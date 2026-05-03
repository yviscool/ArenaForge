from __future__ import annotations

from typing import Any, Optional

import sublime

_FALLBACKS = {
    "product.name": "ArenaForge",
    "status.settings_loaded": "settings loaded",
    "status.compiled": "Compiled",
    "status.process_already_running": "process already running",
    "status.stop_process_before_delete": "stop process before delete action",
    "status.tests_deleted": "deleted tests: {tests}",
    "status.action_while_running": "cannot {action} while process is running",
    "status.debugger_enabled": "debugger enabled",
    "status.debugger_disabled": "debugger disabled",
    "status.nothing_to_show": "nothing to show",
    "status.sense_enabled": "sense enabled",
    "status.sense_disabled": "sense disabled",
    "status.stressing_test": "stressing, test: {test_id}",
    "status.stress_stopped": "stress stopped",
    "status.session_saved": "session saved",
    "status.credentials_saved": "credentials saved for {provider}",
    "status.submitting": "submitting to {provider}",
    "status.submission_complete": "submission sent to {provider}",
    "status.history_empty": "run history is empty",
    "status.compile_issue": "error:{line}:{column}: {message}",
    "status.doctor_report_ready": "doctor report ready",
    "error.session_restore_failed": "Can't restore session",
    "error.submission_dependencies_unavailable": "submission dependencies are unavailable",
    "error.contest_settings_missing": "_contest.sublime-settings is not found",
    "error.parse_errors_failed": "can not parse errors",
    "error.process_termination_failed": "process terminating error",
    "error.file_not_found": "{file} not found",
    "error.conflict_files": "conflict files: {files}",
    "error.credential_backend_unavailable": "secure credential storage is unavailable",
    "error.credentials_missing": "credentials are required for {provider}",
    "error.provider_submission_unsupported": "{provider} does not support submission yet",
    "error.submission_language_unsupported": "{language} is not configured for {provider} submission",
    "error.submission_failed": "submission failed",
    "error.active_view_required": "an active view is required",
    "error.file_view_required": "open a source file first",
    "prompt.contest_url": "Contest URL",
    "prompt.credential_username": "{provider} username",
    "prompt.credential_secret": "{provider} password or token",
    "command.configure_credentials": "Configure Credentials",
    "command.doctor": "Doctor",
    "command.run_history": "Run History",
    "result.matches_expected": "matches expected output",
    "result.matches_rejected": "matches known rejected output",
    "result.first_mismatch": "first mismatch at line {line}, column {column}",
    "result.no_expected_output": "no expected output configured",
    "ui.test": "test",
    "ui.edit": "edit",
    "ui.run": "run",
    "ui.stop": "stop",
    "ui.next_test": "next test",
    "ui.save": "save",
    "ui.delete": "delete",
    "ui.time": "time",
    "ui.result": "result",
    "ui.accept": "accept",
    "ui.decline": "decline",
    "ui.expected": "expected",
    "ui.actual": "actual",
    "ui.run_history": "Run History",
}

_STATUS_KEY_BY_CODE = {
    "COMPILED": "status.compiled",
    "COMPILING": "status.compiling",
    "RUNNING": "status.running",
    "STOPPED": "status.stopped",
}


def translate(key: str, locale: Optional[str] = None, **kwargs: Any) -> str:
    normalized = {name: str(value) for name, value in kwargs.items()}
    try:
        from .settings_bridge import get_application

        return get_application().translator.translate(key, locale=locale, **normalized)
    except Exception:
        template = _FALLBACKS.get(key, key)
        return template.format(**normalized)


def status_message(key: str, **kwargs: Any) -> None:
    sublime.status_message(translate(key, **kwargs))


def product_status_message(key: str, **kwargs: Any) -> None:
    sublime.status_message(f"{translate('product.name')}: {translate(key, **kwargs)}")


def product_log_message(key: str, **kwargs: Any) -> None:
    print(f"{translate('product.name')}: {translate(key, **kwargs)}")


def error_message(key: str, **kwargs: Any) -> None:
    sublime.error_message(translate(key, **kwargs))


def product_error_message(key: str, **kwargs: Any) -> None:
    sublime.error_message(f"{translate('product.name')}: {translate(key, **kwargs)}")


def translate_status_code(status_code: str) -> str:
    return translate(_STATUS_KEY_BY_CODE.get(status_code, status_code))
