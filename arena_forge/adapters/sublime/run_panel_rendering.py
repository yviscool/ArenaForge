from __future__ import annotations

from html import escape

from sublime import LAYOUT_BLOCK, Phantom, Region

from .messages import translate
from .render_assets import build_styles, render_template
from .result_display import (
    format_output_evaluation_detail,
    format_output_evaluation_summary,
    result_summary_css_class,
)
from .run_panel_logic import display_test_number


def _build_result_block(state) -> str:
    summary = format_output_evaluation_summary(getattr(state, "last_evaluation", None))
    if not summary:
        return ""
    detail = format_output_evaluation_detail(getattr(state, "last_evaluation", None))
    detail_html = f'<span class="result-detail">{escape(detail)}</span>' if detail else ""
    summary_class = result_summary_css_class(getattr(state, "last_evaluation", None))
    return (
        '<div class="result-summary {summary_class}">'
        '<span class="meta-label">{result_label}</span>'
        '<span class="meta-value">{summary}</span>'
        "{detail_html}"
        "</div>"
    ).format(
        summary_class=summary_class,
        result_label=translate("ui.result"),
        summary=summary,
        detail_html=detail_html,
    )


def build_test_config_phantom(state, test_id, point, callback, output_text, view, running=False):
    styles = build_styles(view)
    display_number = display_test_number(test_id)
    if running:
        content = render_template("test_running.html", test_id=display_number)
    else:
        test_type = ""
        evaluation = getattr(state, "last_evaluation", None)
        if evaluation is not None and evaluation.verdict.value == "accepted":
            test_type = "test-accept"
        elif evaluation is not None and evaluation.verdict.value == "rejected":
            test_type = "test-decline"
        if str(state.rtcode) != "0":
            test_type = "test-decline"
        content = render_template(
            "test_config.html",
            test_id=display_number,
            runtime=state.get_nice_runtime(),
            test_type=test_type,
            result_block=_build_result_block(state),
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
    return Phantom(Region(max(view.size() - 1, 0)), content, LAYOUT_BLOCK, lambda event, cb=callback: cb(event))


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
    content = "<style>" + styles + "</style>" + render_template(
        "test_edit.html",
        test_id=display_test_number(test_id),
    )
    return Phantom(Region(0), content, LAYOUT_BLOCK, callback)
