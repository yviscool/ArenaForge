from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional, Union

from arena_forge.adapters.i18n.catalog import translate_catalog as translate
from arena_forge.core.domain import ContestDescriptor, LanguageProfile, SessionSnapshot

from ..storage.json_repository import JsonSessionRepository
from ..storage.workspace import WorkspaceLayout


class ContestWorkspaceScaffolder:
    def __init__(
        self,
        layout: WorkspaceLayout,
        repository: JsonSessionRepository,
        profiles: tuple[LanguageProfile, ...],
    ):
        self.layout = layout
        self.repository = repository
        self.profiles = profiles

    @staticmethod
    def sanitize_name(value: str) -> str:
        for char in '<>:"/\\|?*':
            value = value.replace(char, "_")
        return value.strip() or "Contest"

    def _profile_for_language(self, language_id: str) -> LanguageProfile:
        normalized = str(language_id).strip().lower()
        for profile in self.profiles:
            if normalized in {profile.identifier.lower(), profile.name.strip().lower()}:
                return profile
        raise ValueError(translate("error.unsupported_contest_language", language_id=language_id))

    def _template_text_for_profile(self, profile: LanguageProfile) -> str:
        if not profile.template_path:
            return ""
        package_root = Path(__file__).resolve().parents[2]
        template_path = package_root / profile.template_path
        try:
            return template_path.read_text(encoding="utf-8")
        except OSError:
            return ""

    @staticmethod
    def _render_template(template_text: str, problem_index: str) -> str:
        return (
            template_text
            .replace("__PROBLEM_ID__", problem_index)
            .replace("__CLASS_NAME__", problem_index)
            .replace("__FILE_NAME__", problem_index)
        )

    def scaffold(
        self,
        contests_root: Union[str, Path],
        contest: ContestDescriptor,
        *,
        language_id: str = "cpp",
        template_text: Optional[str] = None,
        progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> Path:
        base = Path(contests_root).expanduser() / contest.provider / self.sanitize_name(contest.title)
        base.mkdir(parents=True, exist_ok=True)
        profile = self._profile_for_language(language_id)
        source_extension = profile.primary_extension
        effective_template_text = (
            self._template_text_for_profile(profile) if template_text is None else template_text
        )

        metadata = {
            "contest_id": contest.contest_id,
            "title": contest.title,
            "provider": contest.provider,
            "problems": [problem.index for problem in contest.problems],
            "language_id": profile.identifier,
        }
        (base / "contest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        (base / "_contest.sublime-settings").write_text(
            json.dumps(
                {"contestID": contest.contest_id, "provider": contest.provider, "language_id": profile.identifier},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        total = len(contest.problems)
        for position, problem in enumerate(contest.problems, start=1):
            source_file = base / f"{problem.index}.{source_extension}"
            if not source_file.exists():
                source_file.write_text(
                    self._render_template(effective_template_text, problem.index),
                    encoding="utf-8",
                )

            session = SessionSnapshot(
                source_file=str(source_file.resolve()),
                language=profile.identifier,
                tests=problem.samples,
            )
            self.repository.save(session)
            self.layout.write_tests_index(
                str(source_file),
                [sample.to_mapping() for sample in problem.samples],
            )
            if progress is not None:
                progress(position, total, problem.index)
        return base
