import unittest

from arena_forge.adapters.providers.atcoder import (
    AtCoderProvider,
    extract_atcoder_contest_title,
    extract_atcoder_samples,
    extract_printed_tasks,
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

PRINT_HTML = """
<html>
  <head>
    <title>AtCoder Beginner Contest 999</title>
  </head>
  <body>
    <div class="col-sm-12">
      <span class="h2">A - Water Station</span>
      <div id="task-statement">
        <span class="lang">
          <span class="lang-ja">
            <h3>入力例 1</h3><pre>ignore</pre>
            <h3>出力例 1</h3><pre>ignore</pre>
          </span>
          <span class="lang-en">
            <h3>Sample Input 1</h3><pre>1 2<br />3</pre>
            <h3>Sample Output 1</h3><pre>6</pre>
          </span>
        </span>
      </div>
    </div>
    <div class="col-sm-12">
      <span class="h2">B - Tree Walk</span>
      <div id="task-statement">
        <span class="lang">
          <span class="lang-en">
            <h3>Sample Input 1</h3><pre>a &lt; b</pre>
            <h3>Sample Output 1</h3><pre>yes</pre>
          </span>
        </span>
      </div>
    </div>
  </body>
</html>
"""


class _FakeAtCoderProvider(AtCoderProvider):
    def __init__(self, payloads):
        super().__init__()
        self.payloads = payloads
        self.urls = []

    def _fetch_text(self, url: str) -> str:
        self.urls.append(url)
        payload = self.payloads[url]
        if isinstance(payload, Exception):
            raise payload
        return payload


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

    def test_extract_printed_tasks_reads_english_samples_per_problem(self) -> None:
        problems = extract_printed_tasks(PRINT_HTML)
        self.assertEqual(tuple(problem.index for problem in problems), ("A", "B"))
        self.assertEqual(tuple(problem.title for problem in problems), ("Water Station", "Tree Walk"))
        self.assertEqual(problems[0].samples[0].input_text, "1 2\n3")
        self.assertEqual(problems[1].samples[0].accepted_outputs, ("yes",))

    def test_load_contest_builds_problem_descriptors(self) -> None:
        provider = _FakeAtCoderProvider(
            {
                "https://atcoder.jp/contests/abc999/tasks_print?lang=en": (
                    "<html><head><title>AtCoder Beginner Contest 999</title></head><body></body></html>"
                ),
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

    def test_load_contest_prefers_print_page_when_available(self) -> None:
        provider = _FakeAtCoderProvider(
            {
                "https://atcoder.jp/contests/abc999/tasks_print?lang=en": PRINT_HTML,
            }
        )
        contest = provider.load_contest("abc999")
        self.assertEqual(contest.title, "AtCoder Beginner Contest 999")
        self.assertEqual(tuple(problem.index for problem in contest.problems), ("A", "B"))
        self.assertEqual(provider.urls, ["https://atcoder.jp/contests/abc999/tasks_print?lang=en"])

    def test_load_contest_falls_back_when_print_page_request_fails(self) -> None:
        provider = _FakeAtCoderProvider(
            {
                "https://atcoder.jp/contests/abc999/tasks_print?lang=en": RuntimeError("boom"),
                "https://atcoder.jp/contests/abc999/tasks?lang=en": TASKS_HTML,
                "https://atcoder.jp/contests/abc999/tasks/abc999_a?lang=en": TASK_HTML,
                "https://atcoder.jp/contests/abc999/tasks/abc999_b?lang=en": TASK_HTML,
            }
        )

        contest = provider.load_contest("abc999")

        self.assertEqual(contest.title, "AtCoder Beginner Contest 999")
        self.assertEqual(tuple(problem.index for problem in contest.problems), ("A", "B"))


if __name__ == "__main__":
    unittest.main()
