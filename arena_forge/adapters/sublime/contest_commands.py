from __future__ import annotations

from os import path

import sublime
import sublime_plugin
from sublime import Region

from arena_forge.adapters.providers.submission_service import (
    MissingCredentialsError,
    SubmissionRequest,
    SubmissionServiceError,
)

from .messages import product_log_message, product_status_message, translate
from .settings_bridge import get_application, get_contests_root


class ContestHandlerCommand(sublime_plugin.TextCommand):
    def _open_contest_workspace(self, base):
        sublime.run_command("new_window")
        sublime.active_window().set_project_data({"folders": [{"path": str(base)}]})

    def try_init_contest(self, url):
        app = get_application()
        resolved = app.provider_registry.resolve_url(url)
        descriptor = resolved.provider.load_contest(resolved.contest_id)
        base = app.workspace_scaffolder.scaffold(get_contests_root(), descriptor)
        sublime.set_timeout(lambda base=base: self._open_contest_workspace(base))

    def _read_contest_settings(self):
        for folder in self.view.window().folders():
            file = path.join(folder, "_contest.sublime-settings")
            if path.exists(file):
                return sublime.decode_value(open(file).read())
        return None

    def _prompt_and_store_credentials(self, provider_name: str, retry) -> None:
        app = get_application()
        credential_store = app.credential_store
        if not credential_store.is_available():
            product_log_message("error.credential_backend_unavailable")
            return

        def on_secret(secret: str, username: str) -> None:
            credential_store.set_credentials(provider_name, username, secret)
            product_status_message("status.credentials_saved", provider=provider_name)
            retry()

        def on_username(username: str) -> None:
            self.view.window().show_input_panel(
                translate("prompt.credential_secret", provider=provider_name),
                "",
                lambda secret, username=username: on_secret(secret, username),
                lambda _: None,
                lambda: None,
            )

        self.view.window().show_input_panel(
            translate("prompt.credential_username", provider=provider_name),
            "",
            on_username,
            lambda _: None,
            lambda: None,
        )

    def _submit_current_view(self) -> None:
        app = get_application()
        settings = self._read_contest_settings()
        if settings is None:
            product_log_message("error.contest_settings_missing")
            return

        provider_name = str(settings["provider"])
        code = self.view.substr(Region(0, int(1e9)))
        last = path.basename(self.view.file_name())
        problem_id = path.splitext(last)[0]
        language_name = app.session_service.ensure_session(self.view.file_name(), app.profiles).language
        request = SubmissionRequest(
            provider_name=provider_name,
            contest_id=str(settings["contestID"]),
            problem_id=problem_id,
            language_name=language_name,
            code=code,
        )

        def do_submit() -> None:
            try:
                product_status_message("status.submitting", provider=provider_name)
                app.submission_service.submit(request)
                product_status_message("status.submission_complete", provider=provider_name)
            except MissingCredentialsError:
                self._prompt_and_store_credentials(provider_name, do_submit)
            except SubmissionServiceError as exc:
                product_log_message(exc.message_key, **exc.context)

    def run(self, edit, action=None):
        if action == "setup_contest":
            def on_done(url, self=self):
                sublime.set_timeout_async(lambda self=self, url=url: self.try_init_contest(url))

            self.view.window().show_input_panel(
                translate("prompt.contest_url"),
                "https://codeforces.com/contest/1056/problem/C or https://atcoder.jp/contests/abc400/tasks/abc400_a",
                on_done,
                lambda url: None,
                lambda: None,
            )
            return

        if action == "configure_credentials":
            settings = self._read_contest_settings()
            if settings is None:
                product_log_message("error.contest_settings_missing")
                return
            provider_name = str(settings["provider"])
            self._prompt_and_store_credentials(provider_name, lambda: None)
            return

        if action == "submit":
            sublime.set_timeout_async(self._submit_current_view, 10)
