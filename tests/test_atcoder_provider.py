import unittest

from arena_forge.adapters.providers.atcoder import (
    AtCoderProvider,
    extract_atcoder_contest_title,
    extract_atcoder_samples,
    extract_task_summaries,
)

TASKS_HTML = """
<html>
  <head>
    <title>Tasks - AtCoder Beginner Contest 999 - AtCoder</title>
  </head>
  <body>
    <table>
      <tr>
        <td><a href="/contests/abc999/tasks/abc999_a">A</a></td>
        <td><a href="/contests/abc999/tasks/abc999_a">Water Station</a></td>
      </tr>
      <tr>
        <td><a href="/contests/abc999/tasks/abc999_b">B</a></td>
        <td><a href="/contests/abc999/tasks/abc999_b">Tree Walk</a></td>
      </tr>
    </table>
  </body>
</html>
"""

TASK_HTML = """
<html>
  <body>
    <section>
      <h3>Sample Input 1</h3>
      <pre>1 2<br />3</pre>
      <h3>Sample Output 1</h3>
      <pre>6</pre>
      <h3>Sample Input 2</h3>
      <pre>a &lt; b</pre>
      <h3>Sample Output 2</h3>
      <pre>yes</pre>
    </section>
  </body>
</html>
"""


class _FakeAtCoderProvider(AtCoderProvider):
    def __init__(self, payloads):
        super().__init__()
        self.payloads = payloads

    def _fetch_text(self, url: str) -> str:
        return self.payloads[url]


class AtCoderProviderTests(unittest.TestCase):
    def test_extract_task_summaries_keeps_index_title_and_url(self) -> None:
        tasks = extract_task_summaries(TASKS_HTML, "abc999")
        self.assertEqual(tasks[0].index, "A")
        self.assertEqual(tasks[0].title, "Water Station")
        self.assertTrue(tasks[0].url.endswith("/contests/abc999/tasks/abc999_a"))
        self.assertEqual(tasks[1].index, "B")

    def test_extract_atcoder_samples_supports_br_and_entities(self) -> None:
        self.assertEqual(
            extract_atcoder_samples(TASK_HTML),
            (("1 2\n3", "6"), ("a < b", "yes")),
        )

    def test_extract_atcoder_contest_title_strips_wrapper(self) -> None:
        self.assertEqual(
            extract_atcoder_contest_title(TASKS_HTML, "abc999"),
            "AtCoder Beginner Contest 999",
        )

    def test_load_contest_builds_problem_descriptors(self) -> None:
        provider = _FakeAtCoderProvider(
            {
                "https://atcoder.jp/contests/abc999/tasks?lang=en": TASKS_HTML,
                "https://atcoder.jp/contests/abc999/tasks/abc999_a?lang=en": TASK_HTML,
                "https://atcoder.jp/contests/abc999/tasks/abc999_b?lang=en": TASK_HTML,
            }
        )
        contest = provider.load_contest("abc999")
        self.assertEqual(contest.provider, "atcoder")
        self.assertEqual(contest.title, "AtCoder Beginner Contest 999")
        self.assertEqual(tuple(problem.index for problem in contest.problems), ("A", "B"))
        self.assertEqual(contest.problems[0].samples[0].name, "A-1")


if __name__ == "__main__":
    unittest.main()
