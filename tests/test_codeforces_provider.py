import unittest

from arena_forge.adapters.providers.codeforces import (
    CodeforcesProvider,
    extract_contest_title,
    extract_problem_summaries,
    extract_samples,
)

HTML = """
<html>
  <head>
    <title>Example Round 999 - Codeforces</title>
  </head>
  <body>
    <div class="sample-test">
      <div class="input">
        <div class="title">Input</div>
        <pre>1<br />2</pre>
      </div>
      <div class="output">
        <div class="title">Output</div>
        <pre>3</pre>
      </div>
      <div class="input">
        <div class="title">Input</div>
        <pre>a &lt; b</pre>
      </div>
      <div class="output">
        <div class="title">Output</div>
        <pre>YES</pre>
      </div>
    </div>
  </body>
</html>
"""

CONTEST_HTML = """
<html>
  <head>
    <title>Example Round 999 - Codeforces</title>
  </head>
  <body>
    <table class="problems">
      <tr>
        <td class="id"><a href="/contest/999/problem/A">A</a></td>
        <td class="name"><a href="/contest/999/problem/A">Alpha</a></td>
      </tr>
      <tr>
        <td class="id"><a href="/problemset/problem/999/B">B</a></td>
        <td class="name"><a href="/problemset/problem/999/B">Beta</a></td>
      </tr>
    </table>
  </body>
</html>
"""


class _FakeCodeforcesProvider(CodeforcesProvider):
    def __init__(self, payloads):
        super().__init__()
        self.payloads = payloads
        self.urls = []

    def _fetch_text(self, url: str) -> str:
        self.urls.append(url)
        return self.payloads[url]


class CodeforcesProviderTests(unittest.TestCase):
    def test_extract_samples_supports_br_and_entities(self) -> None:
        self.assertEqual(
            extract_samples(HTML),
            (("1\n2", "3"), ("a < b", "YES")),
        )

    def test_extract_contest_title_uses_html_title(self) -> None:
        self.assertEqual(extract_contest_title(HTML, "999"), "Example Round 999")

    def test_extract_problem_summaries_keeps_exact_problem_order(self) -> None:
        problems = extract_problem_summaries(CONTEST_HTML, "999")
        self.assertEqual(tuple(problem.index for problem in problems), ("A", "B"))
        self.assertEqual(tuple(problem.title for problem in problems), ("Alpha", "Beta"))

    def test_load_contest_uses_problem_listing_instead_of_alpha_probe(self) -> None:
        provider = _FakeCodeforcesProvider(
            {
                "https://codeforces.com/contest/999": CONTEST_HTML,
                "https://codeforces.com/contest/999/problem/A": HTML,
                "https://codeforces.com/contest/999/problem/B": HTML,
            }
        )
        progress_events = []
        contest = provider.load_contest(
            "999",
            progress=lambda completed, total, problem: progress_events.append((completed, total, problem)),
        )
        self.assertEqual(contest.title, "Example Round 999")
        self.assertEqual(tuple(problem.index for problem in contest.problems), ("A", "B"))
        self.assertEqual(tuple(problem.title for problem in contest.problems), ("Alpha", "Beta"))
        self.assertEqual({problem for _, _, problem in progress_events}, {"A", "B"})
        self.assertEqual(sorted(completed for completed, _, _ in progress_events), [1, 2])
        self.assertEqual(
            set(provider.urls),
            {
                "https://codeforces.com/contest/999",
                "https://codeforces.com/contest/999/problem/A",
                "https://codeforces.com/contest/999/problem/B",
            },
        )


if __name__ == "__main__":
    unittest.main()
