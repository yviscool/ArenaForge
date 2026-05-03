import unittest

from arena_forge.adapters.providers.codeforces_submit import (
    STATIC_BFAA,
    build_login_payload,
    build_submit_payload,
    extract_csrf_token,
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


if __name__ == "__main__":
    unittest.main()
