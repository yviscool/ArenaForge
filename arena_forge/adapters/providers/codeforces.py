from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Iterable, List, Optional, Tuple
from urllib.request import Request, urlopen

from arena_forge.core.domain import (
    ContestDescriptor,
    ContestProblem,
    CredentialRecord,
    ProviderCapabilities,
    ProviderWorkspaceKind,
    TestCase,
)

from .codeforces_submit import login as login_codeforces
from .codeforces_submit import submit as submit_codeforces

USER_AGENT = "ArenaForge/3.0 (+https://example.invalid)"


class _SamplesParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.samples: List[Tuple[str, str]] = []
        self._active_side: Optional[str] = None
        self._active_depth = 0
        self._in_pre = False
        self._current_input: List[str] = []
        self._current_output: List[str] = []

    def handle_starttag(self, tag: str, attrs: Iterable[Tuple[str, Optional[str]]]) -> None:
        attrs_map = {key: value or "" for key, value in attrs}
        class_name = attrs_map.get("class", "")
        if tag == "div" and "input" in class_name.split() and self._active_side is None:
            self._active_side = "input"
            self._active_depth = 1
        elif tag == "div" and "output" in class_name.split() and self._active_side is None:
            self._active_side = "output"
            self._active_depth = 1
        elif tag == "div" and self._active_side:
            self._active_depth += 1
        elif tag == "pre" and self._active_side:
            self._in_pre = True
        elif tag == "br" and self._in_pre:
            self._push("\n")

    def handle_startendtag(self, tag: str, attrs: Iterable[Tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre":
            self._in_pre = False
        elif tag == "div" and self._active_side:
            self._active_depth -= 1
            if self._active_depth == 0:
                if self._active_side == "output":
                    input_text = self._flush(self._current_input)
                    output_text = self._flush(self._current_output)
                    if input_text or output_text:
                        self.samples.append((input_text, output_text))
                self._active_side = None

    def handle_data(self, data: str) -> None:
        if self._in_pre:
            self._push(data)

    def handle_entityref(self, name: str) -> None:
        if self._in_pre:
            self._push(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._in_pre:
            self._push(f"&#{name};")

    def _push(self, value: str) -> None:
        if self._active_side == "input":
            self._current_input.append(value)
        elif self._active_side == "output":
            self._current_output.append(value)

    @staticmethod
    def _flush(chunks: list[str]) -> str:
        text = unescape("".join(chunks)).replace("\r\n", "\n").strip()
        chunks.clear()
        return text


def extract_samples(html: str) -> tuple[tuple[str, str], ...]:
    parser = _SamplesParser()
    parser.feed(html)
    return tuple(parser.samples)


def extract_contest_title(html: str, contest_id: str) -> str:
    opening = "<title>"
    closing = "</title>"
    start = html.find(opening)
    end = html.find(closing, start + len(opening))
    if start != -1 and end != -1:
        title = unescape(html[start + len(opening) : end]).strip()
        title = title.replace(" - Codeforces", "").replace(" - Educational Codeforces Round", "")
        if title:
            return title
    return f"Codeforces Contest {contest_id}"


@dataclass(frozen=True)
class CodeforcesProvider:
    provider_name: str = "codeforces"
    capabilities: ProviderCapabilities = ProviderCapabilities(
        workspace_kind=ProviderWorkspaceKind.CONTEST,
        supports_submission=True,
        requires_credentials=True,
    )

    def _fetch_text(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8", "replace")

    def load_problem_samples(self, contest_id: str, problem_id: str) -> tuple[TestCase, ...]:
        url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_id}"
        html = self._fetch_text(url)
        samples = extract_samples(html)
        return tuple(
            TestCase(
                name=f"{problem_id}-{index + 1}",
                input_text=input_text,
                accepted_outputs=(output_text,),
            )
            for index, (input_text, output_text) in enumerate(samples)
        )

    def load_contest_title(self, contest_id: str) -> str:
        html = self._fetch_text(f"https://codeforces.com/contest/{contest_id}")
        return extract_contest_title(html, contest_id)

    def load_contest(self, contest_id: str) -> ContestDescriptor:
        title = self.load_contest_title(contest_id)
        problems = []
        for problem_id in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            samples = self.load_problem_samples(contest_id, problem_id)
            if not samples:
                break
            problems.append(ContestProblem(index=problem_id, title=problem_id, samples=samples))
        return ContestDescriptor(
            contest_id=str(contest_id),
            title=title,
            provider=self.provider_name,
            problems=tuple(problems),
        )

    def submit_solution(
        self,
        contest_id: str,
        problem_id: str,
        language_id: int,
        code: str,
        credentials: CredentialRecord,
    ) -> None:
        from .codeforces_submit import requests

        if requests is None:
            raise ModuleNotFoundError("requests is required for Codeforces submission support")
        session = requests.Session()
        login_codeforces(
            session,
            {"username": credentials.username, "password": credentials.secret},
        )
        submit_codeforces(session, str(contest_id), str(problem_id), int(language_id), code)
