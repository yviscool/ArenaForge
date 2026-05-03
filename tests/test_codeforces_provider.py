import unittest

from arena_forge.adapters.providers.codeforces import extract_contest_title, extract_samples

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


class CodeforcesProviderTests(unittest.TestCase):
    def test_extract_samples_supports_br_and_entities(self) -> None:
        self.assertEqual(
            extract_samples(HTML),
            (("1\n2", "3"), ("a < b", "YES")),
        )

    def test_extract_contest_title_uses_html_title(self) -> None:
        self.assertEqual(extract_contest_title(HTML, "999"), "Example Round 999")


if __name__ == "__main__":
    unittest.main()
