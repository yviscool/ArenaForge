from __future__ import annotations

from typing import Optional, Sequence

from arena_forge.adapters.i18n.catalog import translate_catalog as translate
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
    def from_language_profiles(
        cls,
        language_profiles: Sequence[LanguageProfile],
        platform_name: str,
        timeout_seconds=None,
    ):
        profiles = tuple(language_profiles)
        return cls(profiles=profiles, platform_name=platform_name, timeout_seconds=timeout_seconds)

    from_settings = from_language_profiles

    def profile_for_language(self, language: str) -> LanguageProfile:
        normalized = str(language).strip().lower()
        for profile in self.profiles:
            if normalized in {
                profile.identifier.lower(),
                profile.name.strip().lower(),
                str(profile.submission_key or "").strip().lower(),
            }:
                return profile
        raise ValueError(translate("error.unsupported_language_profile", language=language))

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
