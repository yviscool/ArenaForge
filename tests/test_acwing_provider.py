import unittest

from arena_forge.adapters.providers.acwing import AcWingProvider, extract_acwing_samples, extract_acwing_title

HTML = """
<html>
  <head>
    <title>1. A + B - AcWing</title>
  </head>
  <body>
    <section>
      <h3>输入样例：</h3>
      <pre>1 2</pre>
      <h3>输出样例：</h3>
      <pre>3</pre>
      <h3>Sample Input 2</h3>
      <pre>a &lt; b</pre>
      <h3>Sample Output 2</h3>
      <pre>yes</pre>
    </section>
  </body>
</html>
"""


class _FakeAcWingProvider(AcWingProvider):
    def _fetch_text(self, url: str) -> str:
        return HTML


class AcWingProviderTests(unittest.TestCase):
    def test_extract_acwing_title(self) -> None:
        self.assertEqual(extract_acwing_title(HTML, "1"), "1. A + B")

    def test_extract_acwing_samples(self) -> None:
        self.assertEqual(extract_acwing_samples(HTML), (("1 2", "3"), ("a < b", "yes")))

    def test_load_contest_builds_single_problem_descriptor(self) -> None:
        contest = _FakeAcWingProvider().load_contest("1")
        self.assertEqual(contest.provider, "acwing")
        self.assertEqual(contest.problems[0].index, "1")
        self.assertEqual(contest.problems[0].samples[1].accepted_outputs, ("yes",))


if __name__ == "__main__":
    unittest.main()
