from __future__ import annotations

import time
from html.parser import HTMLParser
from random import choice
from string import ascii_letters, digits
from typing import Optional
from urllib.parse import quote

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - optional Sublime dependency
    requests = None


CODEFORCES_LOGIN_URL = "https://codeforces.com/enter"
CODEFORCES_SUBMIT_URL = "https://codeforces.com/contest/{contest_id}/submit"
CODEFORCES_STATUS_API_URL = "https://codeforces.com/api/user.status?handle={handle}&from=1&count={count}"
DEFAULT_LANGUAGE_ID = 54
DEFAULT_HTTP_TIMEOUT_SECONDS = 15
DEFAULT_CONFIRMATION_TIMEOUT_SECONDS = 10.0
DEFAULT_CONFIRMATION_POLL_INTERVAL_SECONDS = 1.0
DEFAULT_STATUS_LOOKBACK = 10
STATIC_BFAA = "f1b3f18c715565b589b7823cda7448ce"


class CodeforcesSubmissionError(ValueError):
    pass


class _CsrfTokenParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.token: Optional[str] = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag != "meta" or self.token is not None:
            return
        attrs_map = dict(attrs)
        if attrs_map.get("name") == "X-Csrf-Token":
            self.token = attrs_map.get("content")


def random_string(length: int) -> str:
    return "".join(choice(ascii_letters + digits) for _ in range(length))


def generate_ftaa() -> str:
    return random_string(18)


def extract_csrf_token(html: str) -> str:
    parser = _CsrfTokenParser()
    parser.feed(html)
    if parser.token is None:
        raise ValueError("Codeforces csrf token is missing from response HTML")
    return parser.token


def fetch_csrf_token(session, url: str) -> str:
    response = session.get(url, timeout=DEFAULT_HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    return extract_csrf_token(response.text)


def _status_api_url(username: str, *, count: int) -> str:
    return CODEFORCES_STATUS_API_URL.format(handle=quote(username, safe=""), count=count)


def _recent_submissions(session, username: str, *, count: int = DEFAULT_STATUS_LOOKBACK) -> list[dict[str, object]]:
    response = session.get(_status_api_url(username, count=count), timeout=DEFAULT_HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as exc:
        raise CodeforcesSubmissionError("Codeforces status API returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise CodeforcesSubmissionError("Codeforces status API returned an invalid payload")
    if payload.get("status") != "OK":
        comment = str(payload.get("comment") or "unknown status API failure")
        raise CodeforcesSubmissionError(f"Codeforces status API error: {comment}")
    result = payload.get("result")
    if not isinstance(result, list):
        raise CodeforcesSubmissionError("Codeforces status API payload is missing the result list")
    return [entry for entry in result if isinstance(entry, dict)]


def _submission_id(entry: dict[str, object]) -> Optional[int]:
    value = entry.get("id")
    return value if isinstance(value, int) else None


def fetch_latest_submission_id(session, username: str) -> Optional[int]:
    submissions = _recent_submissions(session, username, count=1)
    if not submissions:
        return None
    return _submission_id(submissions[0])


def _matches_submission(
    entry: dict[str, object],
    *,
    contest_id: str,
    problem_id: str,
    previous_latest_submission_id: Optional[int],
    submitted_after: int,
) -> bool:
    if str(entry.get("contestId") or "") != str(contest_id):
        return False
    problem = entry.get("problem")
    if not isinstance(problem, dict):
        return False
    if str(problem.get("index") or "").strip() != str(problem_id):
        return False

    submission_id = _submission_id(entry)
    if previous_latest_submission_id is not None and submission_id is not None:
        return submission_id > previous_latest_submission_id

    created_at = entry.get("creationTimeSeconds")
    return isinstance(created_at, int) and created_at >= submitted_after


def confirm_submission(
    session,
    username: str,
    contest_id: str,
    problem_id: str,
    *,
    previous_latest_submission_id: Optional[int],
    submitted_after: int,
    confirmation_timeout_seconds: float = DEFAULT_CONFIRMATION_TIMEOUT_SECONDS,
    poll_interval_seconds: float = DEFAULT_CONFIRMATION_POLL_INTERVAL_SECONDS,
) -> None:
    deadline = time.monotonic() + max(0.0, float(confirmation_timeout_seconds))
    while True:
        submissions = _recent_submissions(session, username, count=DEFAULT_STATUS_LOOKBACK)
        for entry in submissions:
            if _matches_submission(
                entry,
                contest_id=contest_id,
                problem_id=problem_id,
                previous_latest_submission_id=previous_latest_submission_id,
                submitted_after=submitted_after,
            ):
                return
        if time.monotonic() >= deadline:
            break
        time.sleep(max(0.0, float(poll_interval_seconds)))
    raise CodeforcesSubmissionError(
        f"Codeforces did not confirm the submission for contest {contest_id} problem {problem_id}"
    )


def build_login_payload(*, csrf_token: str, ftaa: str, bfaa: str, username: str, password: str) -> dict[str, str]:
    return {
        "csrf_token": csrf_token,
        "action": "enter",
        "ftaa": ftaa,
        "bfaa": bfaa,
        "handleOrEmail": username,
        "password": password,
        "_tta": "176",
        "remember": "on",
    }


def build_submit_payload(
    *,
    csrf_token: str,
    ftaa: str,
    bfaa: str,
    problem_id: str,
    language_id: int,
    source: str,
) -> dict[str, str]:
    return {
        "csrf_token": csrf_token,
        "ftaa": ftaa,
        "bfaa": bfaa,
        "action": "submitSolutionFormSubmitted",
        "submittedProblemIndex": problem_id,
        "programTypeId": str(language_id),
        "source": source,
        "tabSize": "4",
        "_tta": "594",
        "sourceCodeConfirmed": "true",
    }


def login(session, user: dict[str, str]) -> None:
    csrf_token = fetch_csrf_token(session, CODEFORCES_LOGIN_URL)
    session.ftaa = generate_ftaa()
    session.bfaa = STATIC_BFAA
    response = session.post(
        CODEFORCES_LOGIN_URL,
        data=build_login_payload(
            csrf_token=csrf_token,
            ftaa=session.ftaa,
            bfaa=session.bfaa,
            username=user["username"],
            password=user["password"],
        ),
        timeout=DEFAULT_HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()


def submit(
    session,
    contest_id: str,
    problem_id: str,
    language_id: int,
    source: str,
) -> None:
    submit_url = CODEFORCES_SUBMIT_URL.format(contest_id=contest_id)
    csrf_token = fetch_csrf_token(session, submit_url)
    response = session.post(
        submit_url,
        data=build_submit_payload(
            csrf_token=csrf_token,
            ftaa=session.ftaa,
            bfaa=session.bfaa,
            problem_id=problem_id,
            language_id=language_id,
            source=source,
        ),
        timeout=DEFAULT_HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()


def submit_and_confirm(
    session,
    username: str,
    contest_id: str,
    problem_id: str,
    language_id: int,
    source: str,
    *,
    confirmation_timeout_seconds: float = DEFAULT_CONFIRMATION_TIMEOUT_SECONDS,
    poll_interval_seconds: float = DEFAULT_CONFIRMATION_POLL_INTERVAL_SECONDS,
) -> None:
    previous_latest_submission_id = fetch_latest_submission_id(session, username)
    submitted_after = int(time.time())
    submit(session, contest_id, problem_id, language_id, source)
    confirm_submission(
        session,
        username,
        contest_id,
        problem_id,
        previous_latest_submission_id=previous_latest_submission_id,
        submitted_after=submitted_after,
        confirmation_timeout_seconds=confirmation_timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )


def perform_submission(contest_id: str, problem_id: str, code: str, user: dict[str, str]) -> None:
    if requests is None:
        raise ModuleNotFoundError("requests is required for Codeforces submission support")
    session = requests.Session()
    login(session, user)
    submit_and_confirm(
        session,
        user["username"],
        str(contest_id),
        str(problem_id),
        DEFAULT_LANGUAGE_ID,
        code,
    )


def get_submission_callable():
    if requests is None:
        return None
    return perform_submission
