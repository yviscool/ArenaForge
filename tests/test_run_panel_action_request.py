import unittest

from arena_forge.adapters.sublime.run_panel.action_request import RunPanelActionRequest


class RunPanelActionRequestTests(unittest.TestCase):
    def test_constructor_preserves_dispatch_payload(self) -> None:
        request = RunPanelActionRequest(
            action="make_opd",
            run_file="main.cpp",
            build_sys="source.c++",
            text="hello",
            clr_tests=True,
            sync_out=True,
            code_view_id=9,
            var_name="value",
            use_debugger=True,
            pos=13,
            load_session=True,
            region=(1, 3),
            frame_id=4,
            data={"sample": 1},
            id=7,
            dir=-1,
        )

        self.assertEqual(request.action, "make_opd")
        self.assertEqual(request.run_file, "main.cpp")
        self.assertEqual(request.build_sys, "source.c++")
        self.assertEqual(request.text, "hello")
        self.assertTrue(request.clr_tests)
        self.assertTrue(request.sync_out)
        self.assertEqual(request.code_view_id, 9)
        self.assertEqual(request.var_name, "value")
        self.assertTrue(request.use_debugger)
        self.assertEqual(request.pos, 13)
        self.assertTrue(request.load_session)
        self.assertEqual(request.region, (1, 3))
        self.assertEqual(request.frame_id, 4)
        self.assertEqual(request.data, {"sample": 1})
        self.assertEqual(request.id, 7)
        self.assertEqual(request.dir, -1)

    def test_to_command_args_keeps_only_launch_fields(self) -> None:
        request = RunPanelActionRequest(
            action="make_opd",
            run_file="main.cpp",
            build_sys="source.c++",
            text="ignored",
            clr_tests=True,
            sync_out=False,
            code_view_id=3,
            var_name="ignored",
            use_debugger=True,
            pos=2,
            load_session=True,
            region=(0, 1),
            frame_id=5,
            data="ignored",
            id=8,
            dir=-1,
        )

        self.assertEqual(
            request.to_command_args(),
            {
                "action": "make_opd",
                "run_file": "main.cpp",
                "build_sys": "source.c++",
                "clr_tests": True,
                "sync_out": False,
                "code_view_id": 3,
                "use_debugger": True,
                "load_session": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
