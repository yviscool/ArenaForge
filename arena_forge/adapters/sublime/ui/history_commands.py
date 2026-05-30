from __future__ import annotations

from pathlib import Path

import sublime
import sublime_plugin

from ..shared.messages import translate, translate_verdict
from ..shared.settings_bridge import get_session_repository
from ..support.result_display import (
    format_output_evaluation_detail,
    format_output_evaluation_summary,
)

HISTORY_SOURCE_FILE_KEY = "arena_forge.history_source_file"


def build_history_report(source_file: str, snapshot, *, product_name: str) -> str:
    lines = [f"{product_name}  {translate('ui.run_history')}", f"{translate('ui.file')}: {source_file}", ""]
    if snapshot is None or not snapshot.run_history:
        lines.append(translate("status.history_empty"))
        return "\n".join(lines)
    for item in reversed(snapshot.run_history):
        lines.append(
            "{test_name}  [{verdict}]  {runtime}ms  rc={return_code}".format(
                test_name=item.test_name,
                verdict=translate_verdict(item.verdict),
                runtime=item.runtime_ms,
                return_code=item.return_code,
            )
        )
        summary = format_output_evaluation_summary(item.evaluation)
        detail = format_output_evaluation_detail(item.evaluation)
        if summary:
            lines.append(summary)
        if detail:
            lines.append(detail)
        if item.output_text.strip():
            lines.append(item.output_text.rstrip())
        lines.append("")
    return "\n".join(lines).rstrip()


class RunHistoryPanelCommand(sublime_plugin.TextCommand):
    def run(self, edit) -> None:
        source_file = self.view.file_name()
        if source_file is None:
            sublime.status_message(translate("status.history_empty"))
            return
        snapshot = get_session_repository().load(source_file)
        history_view = self.view.window().new_file()
        history_view.set_name(translate("ui.history_view_title", file_name=Path(source_file).name))
        history_view.set_scratch(True)
        history_view.settings().set(HISTORY_SOURCE_FILE_KEY, source_file)
        history_view.run_command(
            "append",
            {
                "characters": build_history_report(
                    source_file,
                    snapshot,
                    product_name=translate("product.name"),
                )
            },
        )
        history_view.set_read_only(True)


class RunHistoryOpenSourceCommand(sublime_plugin.TextCommand):
    def run(self, edit) -> None:
        source_file = self.view.settings().get(HISTORY_SOURCE_FILE_KEY)
        if not source_file:
            sublime.status_message(translate("status.history_empty"))
            return
        self.view.window().open_file(source_file)
