import unittest

from arena_forge.adapters.providers.acwing import AcWingProvider
from arena_forge.adapters.providers.atcoder import AtCoderProvider
from arena_forge.adapters.providers.codeforces import CodeforcesProvider
from arena_forge.adapters.providers.luogu import LuoguProvider
from arena_forge.adapters.providers.registry import ProviderRegistry


class ProviderRegistryTests(unittest.TestCase):
    def test_registry_resolves_codeforces_url(self) -> None:
        registry = ProviderRegistry()
        registry.register(
            CodeforcesProvider(),
            hosts=("codeforces.com", "www.codeforces.com"),
            contest_id_pattern=r"(?:contest|problemset/problem)/(\d+)|(\d+)",
        )
        resolved = registry.resolve_url("https://codeforces.com/contest/2000/problem/A")
        self.assertEqual(resolved.provider_name, "codeforces")
        self.assertEqual(resolved.contest_id, "2000")

    def test_registry_supports_default_non_capturing_pattern(self) -> None:
        registry = ProviderRegistry()
        registry.register(CodeforcesProvider(), hosts=("codeforces.com",))
        resolved = registry.resolve_url("https://codeforces.com/contest/2001/problem/A")
        self.assertEqual(resolved.contest_id, "2001")

    def test_registry_resolves_atcoder_url(self) -> None:
        registry = ProviderRegistry()
        registry.register(
            AtCoderProvider(),
            hosts=("atcoder.jp", "www.atcoder.jp"),
            contest_id_pattern=r"/contests/([^/?#]+)",
        )
        resolved = registry.resolve_url("https://atcoder.jp/contests/abc400/tasks/abc400_a")
        self.assertEqual(resolved.provider_name, "atcoder")
        self.assertEqual(resolved.contest_id, "abc400")

    def test_registry_resolves_luogu_url(self) -> None:
        registry = ProviderRegistry()
        registry.register(
            LuoguProvider(),
            hosts=("luogu.com.cn", "www.luogu.com.cn"),
            contest_id_pattern=r"/problem/([A-Za-z]\d+)",
        )
        resolved = registry.resolve_url("https://www.luogu.com.cn/problem/P1000")
        self.assertEqual(resolved.provider_name, "luogu")
        self.assertEqual(resolved.contest_id, "P1000")

    def test_registry_resolves_acwing_url(self) -> None:
        registry = ProviderRegistry()
        registry.register(
            AcWingProvider(),
            hosts=("acwing.com", "www.acwing.com"),
            contest_id_pattern=r"/problem/content/(?:description/)?(\d+)",
        )
        resolved = registry.resolve_url("https://www.acwing.com/problem/content/description/1/")
        self.assertEqual(resolved.provider_name, "acwing")
        self.assertEqual(resolved.contest_id, "1")


if __name__ == "__main__":
    unittest.main()
