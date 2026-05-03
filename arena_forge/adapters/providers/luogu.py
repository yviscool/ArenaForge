from __future__ import annotations

import json
from dataclasses import dataclass
from html import unescape
from urllib.request import Request, urlopen

from arena_forge.core.domain import (
    ContestDescriptor,
    ContestProblem,
    CredentialRecord,
    ProviderCapabilities,
    ProviderWorkspaceKind,
    TestCase,
)

USER_AGENT = "ArenaForge/3.0 (+https://example.invalid)"
LUOGU_BASE_URL = "https://www.luogu.com.cn"


def extract_luogu_problem(payload: dict[str, object]) -> tuple[str, str, tuple[TestCase, ...]]:
    current_data = payload.get("currentData", payload)
    problem = current_data.get("problem") if isinstance(current_data, dict) else None
    if not isinstance(problem, dict):
        raise ValueError("Luogu response payload does not include problem data")
    problem_id = str(problem.get("pid") or problem.get("id") or "Problem")
    title = str(problem.get("title") or problem_id)
    samples_payload = problem.get("samples") or ()
    samples: list[TestCase] = []
    for index, sample in enumerate(samples_payload, start=1):
        if not isinstance(sample, dict):
            continue
        input_text = str(sample.get("input") or "")
        output_text = str(sample.get("output") or "")
        samples.append(
            TestCase(
                name=f"{problem_id}-{index}",
                input_text=unescape(input_text).replace("\r\n", "\n").strip(),
                accepted_outputs=(unescape(output_text).replace("\r\n", "\n").strip(),),
            )
        )
    return problem_id, title, tuple(samples)


@dataclass(frozen=True)
class LuoguProvider:
    provider_name: str = "luogu"
    capabilities: ProviderCapabilities = ProviderCapabilities(
        workspace_kind=ProviderWorkspaceKind.PROBLEM,
        supports_submission=False,
        requires_credentials=False,
    )

    def _fetch_payload(self, problem_id: str) -> dict[str, object]:
        url = f"{LUOGU_BASE_URL}/problem/{problem_id}?_contentOnly=1"
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8", "replace"))

    def load_contest(self, contest_id: str) -> ContestDescriptor:
        problem_id, title, samples = extract_luogu_problem(self._fetch_payload(contest_id))
        return ContestDescriptor(
            contest_id=problem_id,
            title=f"{problem_id} {title}",
            provider=self.provider_name,
            problems=(ContestProblem(index=problem_id, title=title, samples=samples),),
        )

    def submit_solution(
        self,
        contest_id: str,
        problem_id: str,
        language_id: int,
        code: str,
        credentials: CredentialRecord,
    ) -> None:
        raise NotImplementedError("Luogu submission is not implemented")
