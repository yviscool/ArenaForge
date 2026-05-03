from __future__ import annotations

from sublime import LAYOUT_BLOCK, Phantom, Region

from .messages import translate
from .render_assets import build_styles, render_template


def build_test_config_phantom(state, test_id, point, callback, output_text, view, running=False):
    styles = build_styles(view)
    if running:
        content = render_template("test_running.html", test_id=test_id)
    else:
        test_type = ""
        if state.is_correct_answer(output_text):
            test_type = "test-accept"
        if str(state.rtcode) != "0":
            test_type = "test-decline"
        content = render_template(
            "test_config.html",
            test_id=test_id,
            runtime=state.get_nice_runtime(),
            test_type=test_type,
        )
    content = "<style>" + styles + "</style>" + content
    return Phantom(Region(point), content, LAYOUT_BLOCK, lambda event, cb=callback, i=test_id: cb(i, event))


def build_accdec_phantom(state, test_id, point, callback, action_type, view):
    styles = build_styles(view)
    content = render_template(
        "test_accdec.html",
        action_label=translate(f"ui.{action_type}"),
        test_id=test_id,
        type=action_type,
        runtime="&nbsp;" * (2 - len(str(state.runtime))) + str(state.runtime),
    )
    content = "<style>" + styles + "</style>" + content
    return Phantom(Region(point), content, LAYOUT_BLOCK, lambda event, cb=callback, i=test_id: cb(i, event))


def build_next_test_title_phantom(view, callback):
    styles = build_styles(view)
    content = render_template("test_next.html")
    content = "<style>" + styles + "</style>" + content
    return Phantom(Region(view.size() - 1), content, LAYOUT_BLOCK, lambda event, cb=callback: cb(event))


def build_compile_bar_phantom(view, cmd, type=""):
    styles = build_styles(view)
    content = render_template(
        "compile.html",
        cmd=cmd,
        type="config-stop" if type == "error" else type,
    )
    content = "<style>" + styles + "</style>" + content
    return Phantom(Region(0), content, LAYOUT_BLOCK)


def build_test_edit_header_phantom(view, test_id, callback):
    styles = build_styles(view)
    content = "<style>" + styles + "</style>" + render_template("test_edit.html", test_id=test_id)
    return Phantom(Region(0), content, LAYOUT_BLOCK, callback)
