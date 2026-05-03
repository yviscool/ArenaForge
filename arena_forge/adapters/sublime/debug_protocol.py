from __future__ import annotations


def supports_variable_inspection(process_manager) -> bool:
    return hasattr(process_manager, "has_var_view_api") and process_manager.has_var_view_api()


def supports_frames(process_manager) -> bool:
    return hasattr(process_manager, "get_frames") and hasattr(process_manager, "select_frame")


def read_frames(process_manager):
    if not supports_frames(process_manager):
        return []
    return process_manager.get_frames()


def select_frame(process_manager, frame_id):
    if supports_frames(process_manager):
        process_manager.select_frame(frame_id)
