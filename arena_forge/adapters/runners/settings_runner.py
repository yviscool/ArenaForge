from __future__ import annotations

from typing import Optional

from arena_forge.core.domain import LanguageProfile
from arena_forge.core.services import select_language_profile

from .subprocess_runner import compile_once, run_once


class SettingsBackedRunner:
    def __init__(
        self,
        profiles: tuple[LanguageProfile, ...],
        platform_name: str,
        timeout_seconds: Optional[float] = None,
    ):
        self.profiles = profiles
        self.platform_name = platform_name
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_settings(cls, run_settings: list[dict[str, object]], platform_name: str, timeout_seconds=None):
        profiles = tuple(LanguageProfile.from_mapping(profile) for profile in run_settings)
        return cls(profiles=profiles, platform_name=platform_name, timeout_seconds=timeout_seconds)

    def profile_for_language(self, language: str) -> LanguageProfile:
        for profile in self.profiles:
            if profile.name == language:
                return profile
        raise ValueError(f"Unsupported language profile: {language}")

    def profile_for_source(self, source_file: str) -> LanguageProfile:
        return select_language_profile(source_file, self.profiles)

    def compile(self, source_file: str, language: str):
        profile = self.profile_for_language(language)
        return compile_once(profile, source_file, platform_name=self.platform_name)

    def run(self, source_file: str, language: str, input_text: str):
        profile = self.profile_for_language(language)
        return run_once(
            profile,
            source_file,
            input_text,
            platform_name=self.platform_name,
            timeout_seconds=self.timeout_seconds,
        )
