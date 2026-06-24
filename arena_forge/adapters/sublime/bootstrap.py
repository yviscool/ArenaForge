from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from arena_forge.adapters.i18n import JsonCatalogTranslator
from arena_forge.adapters.providers import (
    AcWingProvider,
    AtCoderProvider,
    CodeforcesProvider,
    LuoguProvider,
    ProviderRegistry,
    ProviderSubmissionService,
)
from arena_forge.adapters.runners import SettingsBackedRunner
from arena_forge.adapters.security import build_credential_store
from arena_forge.adapters.settings_loader import normalize_settings
from arena_forge.adapters.storage import JsonSessionRepository, WorkspaceLayout
from arena_forge.adapters.workspace import ContestWorkspaceScaffolder
from arena_forge.core.domain import LanguageProfile
from arena_forge.core.usecases import SessionService
from arena_forge.product import PRODUCT_SLUG


@dataclass(frozen=True)
class SublimeApplication:
    settings: dict[str, Any]
    layout: WorkspaceLayout
    profiles: tuple[LanguageProfile, ...]
    repository: JsonSessionRepository
    runner: SettingsBackedRunner
    provider_registry: ProviderRegistry
    credential_store: object
    submission_service: ProviderSubmissionService
    translator: JsonCatalogTranslator
    session_service: SessionService
    workspace_scaffolder: ContestWorkspaceScaffolder


def build_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(CodeforcesProvider())
    registry.register(AtCoderProvider())
    registry.register(LuoguProvider())
    registry.register(AcWingProvider())
    return registry


def build_sublime_application(
    raw_settings: Optional[Mapping[str, Any]],
    *,
    platform_name: str,
    locale_directory: Union[str, Path],
) -> SublimeApplication:
    settings = normalize_settings(raw_settings, platform_name)
    profiles = tuple(LanguageProfile.from_mapping(profile) for profile in settings.get("run_settings", []))
    layout = WorkspaceLayout.from_settings(settings)
    repository = JsonSessionRepository(layout, profiles=profiles)
    runner = SettingsBackedRunner(
        profiles=profiles,
        platform_name=platform_name,
        timeout_seconds=settings.get("stress_time_limit_seconds"),
    )
    provider_registry = build_provider_registry()
    credential_store = build_credential_store(PRODUCT_SLUG)
    submission_service = ProviderSubmissionService(
        provider_registry=provider_registry,
        credential_store=credential_store,
        submission_language_ids=settings.get("submission_language_ids", {}),
    )
    translator = JsonCatalogTranslator(str(locale_directory), default_locale=settings.get("preferred_locale", "en"))
    session_service = SessionService(repository=repository)
    workspace_scaffolder = ContestWorkspaceScaffolder(layout, repository, profiles)
    return SublimeApplication(
        settings=settings,
        layout=layout,
        profiles=profiles,
        repository=repository,
        runner=runner,
        provider_registry=provider_registry,
        credential_store=credential_store,
        submission_service=submission_service,
        translator=translator,
        session_service=session_service,
        workspace_scaffolder=workspace_scaffolder,
    )
