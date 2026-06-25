from __future__ import annotations

import sublime

from arena_forge.core.domain import RunHistoryEntry, SessionSnapshot, Verdict

from ..shared.messages import product_log_message, translate


def persist_panel_tests(source_file, tests, repository, infer_language_name, tests_file_path_factory):
    tests_payload = [test.to_payload() for test in tests]
    encoded_tests = sublime.encode_value(tests_payload, True)
    tests_path = tests_file_path_factory(source_file, for_write=True)
    current_payload = _read_panel_tests_payload(tests_path)
    if current_payload != encoded_tests:
        with open(tests_path, "w", encoding="utf-8") as handle:
            handle.write(encoded_tests)

    language_name = infer_language_name(source_file)
    core_tests = tuple(test.to_test_case(index + 1) for index, test in enumerate(tests))
    snapshot = repository.load(source_file)
    if snapshot is not None and snapshot.language == language_name and snapshot.tests == core_tests:
        return
    session_kwargs = {
        "source_file": source_file,
        "language": language_name,
        "tests": core_tests,
        "run_history": snapshot.run_history if snapshot is not None else (),
    }
    if snapshot is not None:
        session_kwargs["updated_at"] = snapshot.updated_at
    repository.save(
        SessionSnapshot(
            **session_kwargs,
        )
    )


def _read_panel_tests_payload(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


def _decode_panel_tests_payload(payload_text):
    payload = sublime.decode_value(payload_text)
    if not isinstance(payload, list):
        raise ValueError(translate("error.tests_payload_must_be_list"))
    decoded = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(translate("error.test_payload_entries_must_be_objects"))
        if not str(item.get("test", "")).strip():
            continue
        decoded.append(item)
    return decoded


def append_run_history(
    repository,
    source_file,
    test_name,
    output_text,
    verdict,
    runtime_ms,
    return_code,
    evaluation=None,
):
    snapshot = repository.load(source_file)
    if snapshot is None:
        return
    history = list(snapshot.run_history)
    history.append(
        RunHistoryEntry(
            test_name=test_name,
            output_text=output_text,
            verdict=Verdict(verdict) if isinstance(verdict, str) else verdict,
            runtime_ms=runtime_ms,
            return_code=return_code,
            evaluation=evaluation,
        )
    )
    repository.save(
        SessionSnapshot(
            source_file=snapshot.source_file,
            language=snapshot.language,
            tests=snapshot.tests,
            run_history=tuple(history[-50:]),
            updated_at=snapshot.updated_at,
        )
    )


def load_panel_tests(source_file, test_factory, repository, tests_file_path_factory):
    tests_path = tests_file_path_factory(source_file)
    try:
        with open(tests_path, encoding="utf-8") as handle:
            decoded = _decode_panel_tests_payload(handle.read())
        return [test_factory(item) for item in decoded]
    except OSError:
        pass
    except (KeyError, TypeError, ValueError):
        product_log_message("error.tests_file_invalid", path=tests_path)

    snapshot = repository.load(source_file)
    if snapshot is None:
        return []
    return [test_factory(test.to_mapping()) for test in snapshot.tests if test.input_text.strip()]
