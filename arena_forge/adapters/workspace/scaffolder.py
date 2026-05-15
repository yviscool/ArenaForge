from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional, Union

from arena_forge.core.domain import ContestDescriptor, LanguageProfile, SessionSnapshot
from arena_forge.core.services import infer_language

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

    def scaffold(
        self,
        contests_root: Union[str, Path],
        contest: ContestDescriptor,
        *,
        source_extension: str = "cpp",
        template_text: str = "",
        progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> Path:
        base = Path(contests_root).expanduser() / contest.provider / self.sanitize_name(contest.title)
        base.mkdir(parents=True, exist_ok=True)

        metadata = {
            "contest_id": contest.contest_id,
            "title": contest.title,
            "provider": contest.provider,
            "problems": [problem.index for problem in contest.problems],
        }
        (base / "contest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        (base / "_contest.sublime-settings").write_text(
            json.dumps({"contestID": contest.contest_id, "provider": contest.provider}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        language = infer_language(f"placeholder.{source_extension}", self.profiles)
        total = len(contest.problems)
        for position, problem in enumerate(contest.problems, start=1):
            source_file = base / f"{problem.index}.{source_extension}"
            if not source_file.exists():
                source_file.write_text(template_text, encoding="utf-8")

            session = SessionSnapshot(
                source_file=str(source_file.resolve()),
                language=language,
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
