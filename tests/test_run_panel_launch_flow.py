import unittest

from arena_forge.adapters.sublime.run_panel.controller_state import RunPanelLaunchSession
from arena_forge.adapters.sublime.run_panel.launch_flow import (
    RunPanelLaunchRequest,
    plan_run_panel_launch,
)


class RunPanelLaunchFlowTests(unittest.TestCase):
    def test_plan_ignores_launch_while_compiling(self) -> None:
        plan = plan_run_panel_launch(
            status_code="COMPILING",
            request=RunPanelLaunchRequest(run_file="main.cpp"),
            saved_session=None,
        )

        self.assertEqual(plan.action, "noop")

    def test_plan_requests_rerun_when_process_is_running(self) -> None:
        request = RunPanelLaunchRequest(run_file="main.cpp", use_debugger=True, load_session=True)

        plan = plan_run_panel_launch(
            status_code="RUNNING",
            request=request,
            saved_session=None,
        )

        self.assertEqual(plan.action, "rerun")
        self.assertEqual(plan.command_args, request.to_command_args())

    def test_plan_restores_saved_session_when_requested(self) -> None:
        saved_session = RunPanelLaunchSession(
            run_file="saved.cpp",
            build_sys="source.c++",
            clr_tests=False,
            sync_out=True,
            code_view_id=9,
            use_debugger=False,
        )

        plan = plan_run_panel_launch(
            status_code="STOPPED",
            request=RunPanelLaunchRequest(load_session=True),
            saved_session=saved_session,
        )

        self.assertEqual(plan.action, "launch")
        self.assertEqual(plan.session, saved_session)

    def test_plan_reports_restore_error_without_saved_session(self) -> None:
        plan = plan_run_panel_launch(
            status_code="STOPPED",
            request=RunPanelLaunchRequest(load_session=True),
            saved_session=None,
        )

        self.assertEqual(plan.action, "error")
        self.assertEqual(plan.error_key, "error.session_restore_failed")

    def test_plan_builds_fresh_launch_session_for_new_run(self) -> None:
        request = RunPanelLaunchRequest(
            run_file="fresh.cpp",
            build_sys="source.c++",
            clr_tests=True,
            sync_out=False,
            code_view_id=4,
            use_debugger=True,
        )

        plan = plan_run_panel_launch(
            status_code="STOPPED",
            request=request,
            saved_session=None,
        )

        self.assertEqual(plan.action, "launch")
        self.assertEqual(plan.session, request.to_launch_session())


if __name__ == "__main__":
    unittest.main()
