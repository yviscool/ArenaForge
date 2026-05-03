import unittest

from arena_forge.adapters.providers.luogu import LuoguProvider, extract_luogu_problem

PAYLOAD = {
    "currentData": {
        "problem": {
            "pid": "P1000",
            "title": "Super Shell",
            "samples": [
                {"input": "1 2", "output": "3"},
                {"input": "a &lt; b", "output": "yes"},
            ],
        }
    }
}


class _FakeLuoguProvider(LuoguProvider):
    def _fetch_payload(self, problem_id: str) -> dict[str, object]:
        return PAYLOAD


class LuoguProviderTests(unittest.TestCase):
    def test_extract_luogu_problem_maps_samples(self) -> None:
        problem_id, title, samples = extract_luogu_problem(PAYLOAD)
        self.assertEqual(problem_id, "P1000")
        self.assertEqual(title, "Super Shell")
        self.assertEqual(samples[1].input_text, "a < b")

    def test_load_contest_builds_single_problem_descriptor(self) -> None:
        contest = _FakeLuoguProvider().load_contest("P1000")
        self.assertEqual(contest.provider, "luogu")
        self.assertEqual(contest.problems[0].index, "P1000")
        self.assertEqual(contest.problems[0].samples[0].accepted_outputs, ("3",))


if __name__ == "__main__":
    unittest.main()
