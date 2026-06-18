from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from arena_forge.adapters.i18n.catalog import translate_catalog as translate
from arena_forge.core.domain import ProviderCapabilities
from arena_forge.core.ports import ContestProvider


@dataclass(frozen=True)
class ResolvedContestProvider:
    provider_name: str
    provider: ContestProvider
    contest_id: str
    capabilities: ProviderCapabilities


@dataclass(frozen=True)
class _ProviderBinding:
    provider: ContestProvider
    hosts: tuple[str, ...]
    contest_id_pattern: str


class ProviderRegistry:
    def __init__(self):
        self._bindings: dict[str, _ProviderBinding] = {}

    def register(
        self,
        provider: ContestProvider,
        *,
        hosts: tuple[str, ...],
        contest_id_pattern: str = r"\d+",
    ) -> None:
        self._bindings[provider.provider_name] = _ProviderBinding(
            provider=provider,
            hosts=tuple(host.lower() for host in hosts),
            contest_id_pattern=contest_id_pattern,
        )

    def get(self, provider_name: str) -> ContestProvider:
        return self._bindings[provider_name].provider

    def resolve_url(self, url: str) -> ResolvedContestProvider:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        subject = parsed.path or "/"
        for provider_name, binding in self._bindings.items():
            if any(host == candidate or host.endswith("." + candidate) for candidate in binding.hosts):
                match = re.search(binding.contest_id_pattern, subject)
                if match is None:
                    raise ValueError(translate("error.could_not_extract_contest_id", url=url))
                groups = match.groups()
                if groups:
                    contest_id = next((group for group in groups if group), match.group(0))
                else:
                    contest_id = match.group(0)
                return ResolvedContestProvider(
                    provider_name=provider_name,
                    provider=binding.provider,
                    contest_id=contest_id,
                    capabilities=binding.provider.capabilities,
                )
        raise ValueError(translate("error.no_provider_for_host", host=host))
