import unittest

from arena_forge.adapters.providers.codeforces_submit import (
    DEFAULT_HTTP_TIMEOUT_SECONDS,
    STATIC_BFAA,
    CodeforcesSubmissionError,
    build_login_payload,
    build_submit_payload,
    extract_csrf_token,
    fetch_csrf_token,
    login,
    submit,
    submit_and_confirm,
)

HTML = """
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="X-Csrf-Token" content="csrf-123" />
  </head>
</html>
"""


class CodeforcesSubmitTests(unittest.TestCase):
    def test_extract_csrf_token_reads_meta_content(self) -> None:
        self.assertEqual(extract_csrf_token(HTML), "csrf-123")

    def test_build_login_payload_keeps_required_codeforces_fields(self) -> None:
        payload = build_login_payload(
            csrf_token="csrf-123",
            ftaa="ftaa-1",
            bfaa=STATIC_BFAA,
            username="tourist",
            password="secret",
        )
        self.assertEqual(payload["action"], "enter")
        self.assertEqual(payload["handleOrEmail"], "tourist")
        self.assertEqual(payload["bfaa"], STATIC_BFAA)

    def test_build_submit_payload_normalizes_language_and_problem(self) -> None:
        payload = build_submit_payload(
            csrf_token="csrf-123",
            ftaa="ftaa-1",
            bfaa=STATIC_BFAA,
            problem_id="A",
            language_id=54,
            source="int main() {}",
        )
        self.assertEqual(payload["submittedProblemIndex"], "A")
        self.assertEqual(payload["programTypeId"], "54")
        self.assertEqual(payload["sourceCodeConfirmed"], "true")

    def test_fetch_csrf_token_uses_default_timeout(self) -> None:
        class _Response:
            def __init__(self, text: str) -> None:
                self.text = text

            def raise_for_status(self) -> None:
                return None

        class _Session:
            def __init__(self) -> None:
                self.get_calls = []

            def get(self, url: str, timeout: int):
                self.get_calls.append((url, timeout))
                return _Response(HTML)

        session = _Session()
        self.assertEqual(fetch_csrf_token(session, "https://codeforces.com/enter"), "csrf-123")
        self.assertEqual(session.get_calls, [("https://codeforces.com/enter", DEFAULT_HTTP_TIMEOUT_SECONDS)])

    def test_login_and_submit_pass_default_timeout_to_requests(self) -> None:
        class _Response:
            def __init__(self, text: str = HTML) -> None:
                self.text = text

            def raise_for_status(self) -> None:
                return None

        class _Session:
            def __init__(self) -> None:
                self.get_calls = []
                self.post_calls = []

            def get(self, url: str, timeout: int):
                self.get_calls.append((url, timeout))
                return _Response()

            def post(self, url: str, data, timeout: int):
                self.post_calls.append((url, data, timeout))
                return _Response()

        session = _Session()
        login(session, {"username": "tourist", "password": "secret"})
        submit(session, "1000", "A", 54, "print(42)")

        self.assertEqual(session.get_calls[0][1], DEFAULT_HTTP_TIMEOUT_SECONDS)
        self.assertEqual(session.get_calls[1][1], DEFAULT_HTTP_TIMEOUT_SECONDS)
        self.assertEqual(session.post_calls[0][2], DEFAULT_HTTP_TIMEOUT_SECONDS)
        self.assertEqual(session.post_calls[1][2], DEFAULT_HTTP_TIMEOUT_SECONDS)

    def test_submit_and_confirm_accepts_new_submission_seen_via_status_api(self) -> None:
        class _Response:
            def __init__(self, *, text: str = HTML, payload=None) -> None:
                self.text = text
                self._payload = payload

            def raise_for_status(self) -> None:
                return None

            def json(self):
                if self._payload is None:
                    raise AssertionError("json() was not expected")
                return self._payload

        class _Session:
            def __init__(self) -> None:
                self.ftaa = "ftaa-1"
                self.bfaa = STATIC_BFAA
                self.posts = []
                self.status_payloads = [
                    {"status": "OK", "result": [{"id": 100, "contestId": 999, "problem": {"index": "Z"}}]},
                    {"status": "OK", "result": [{"id": 101, "contestId": 1000, "problem": {"index": "A"}}]},
                ]

            def get(self, url: str, timeout: int):
                if "/api/user.status" in url:
                    return _Response(payload=self.status_payloads.pop(0))
                return _Response()

            def post(self, url: str, data, timeout: int):
                self.posts.append((url, data, timeout))
                return _Response()

        session = _Session()
        submit_and_confirm(
            session,
            "tourist",
            "1000",
            "A",
            54,
            "print(42)",
            confirmation_timeout_seconds=0,
            poll_interval_seconds=0,
        )

        self.assertEqual(len(session.posts), 1)
        self.assertEqual(session.posts[0][2], DEFAULT_HTTP_TIMEOUT_SECONDS)

    def test_submit_and_confirm_raises_when_codeforces_never_exposes_a_new_submission(self) -> None:
        class _Response:
            def __init__(self, *, text: str = HTML, payload=None) -> None:
                self.text = text
                self._payload = payload

            def raise_for_status(self) -> None:
                return None

            def json(self):
                if self._payload is None:
                    raise AssertionError("json() was not expected")
                return self._payload

        class _Session:
            def __init__(self) -> None:
                self.ftaa = "ftaa-1"
                self.bfaa = STATIC_BFAA
                self.status_payloads = [
                    {"status": "OK", "result": [{"id": 100, "contestId": 999, "problem": {"index": "Z"}}]},
                    {"status": "OK", "result": [{"id": 100, "contestId": 999, "problem": {"index": "Z"}}]},
                ]

            def get(self, url: str, timeout: int):
                if "/api/user.status" in url:
                    return _Response(payload=self.status_payloads.pop(0))
                return _Response()

            def post(self, url: str, data, timeout: int):
                return _Response()

        session = _Session()
        with self.assertRaises(CodeforcesSubmissionError):
            submit_and_confirm(
                session,
                "tourist",
                "1000",
                "A",
                54,
                "print(42)",
                confirmation_timeout_seconds=0,
                poll_interval_seconds=0,
            )


if __name__ == "__main__":
    unittest.main()
