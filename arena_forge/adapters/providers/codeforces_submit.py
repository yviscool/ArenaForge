from __future__ import annotations

from html.parser import HTMLParser
from random import choice
from string import ascii_letters, digits
from typing import Optional

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - optional Sublime dependency
    requests = None


CODEFORCES_LOGIN_URL = "https://codeforces.com/enter"
CODEFORCES_SUBMIT_URL = "https://codeforces.com/contest/{contest_id}/submit"
DEFAULT_LANGUAGE_ID = 54
DEFAULT_HTTP_TIMEOUT_SECONDS = 15
STATIC_BFAA = "f1b3f18c715565b589b7823cda7448ce"


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


def perform_submission(contest_id: str, problem_id: str, code: str, user: dict[str, str]) -> None:
    if requests is None:
        raise ModuleNotFoundError("requests is required for Codeforces submission support")
    session = requests.Session()
    login(session, user)
    print(f"Logged in as {user['username']}")
    submit(session, str(contest_id), str(problem_id), DEFAULT_LANGUAGE_ID, code)


def get_submission_callable():
    if requests is None:
        return None
    return perform_submission
