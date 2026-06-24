from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

from arena_forge.adapters.i18n.catalog import translate_catalog as translate
from arena_forge.core.domain import (
    ContestDescriptor,
    ContestProblem,
    CredentialRecord,
    ProviderCapabilities,
    ProviderWorkspaceKind,
    TestCase,
)

from .base import extract_html_title, fetch_text, load_items_in_parallel
from .codeforces_submit import login as login_codeforces
from .codeforces_submit import submit_and_confirm as submit_codeforces

CODEFORCES_BASE_URL = "https://codeforces.com"


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


@dataclass(frozen=True)
class ProblemSummary:
    index: str
    title: str
    url: str


@dataclass
class _MutableProblemSummary:
    url: str
    index: str
    title: Optional[str] = None


class _ProblemListParser(HTMLParser):
    def __init__(self, contest_id: str) -> None:
        super().__init__(convert_charrefs=False)
        self.contest_id = contest_id
        self._problems: Dict[str, _MutableProblemSummary] = {}
        self._order: List[str] = []
        self._active_problem_id: Optional[str] = None
        self._active_chunks: List[str] = []

    def handle_starttag(self, tag: str, attrs: Iterable[Tuple[str, Optional[str]]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        problem_id = _problem_id_from_href(href, self.contest_id)
        if problem_id is None:
            return
        self._active_problem_id = problem_id
        self._active_chunks = []

    def handle_data(self, data: str) -> None:
        if self._active_problem_id is not None:
            self._active_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._active_problem_id is None:
            return
        problem_id = self._active_problem_id
        self._active_problem_id = None
        text = " ".join(unescape("".join(self._active_chunks)).split())
        self._active_chunks = []
        if problem_id not in self._problems:
            self._problems[problem_id] = _MutableProblemSummary(
                url=urljoin(CODEFORCES_BASE_URL, f"/contest/{self.contest_id}/problem/{problem_id}"),
                index=problem_id,
            )
            self._order.append(problem_id)
        problem = self._problems[problem_id]
        if text and text != problem.index and problem.title is None:
            problem.title = text

    def finalize(self) -> tuple[ProblemSummary, ...]:
        return tuple(
            ProblemSummary(
                index=problem.index,
                title=problem.title or problem.index,
                url=problem.url,
            )
            for problem_id in self._order
            for problem in (self._problems[problem_id],)
        )


def _problem_id_from_href(href: str, contest_id: str) -> Optional[str]:
    contest_prefix = f"/contest/{contest_id}/problem/"
    problemset_prefix = f"/problemset/problem/{contest_id}/"
    normalized = href.split("?", 1)[0].split("#", 1)[0]
    if normalized.startswith(contest_prefix):
        return normalized[len(contest_prefix) :].strip("/") or None
    if normalized.startswith(problemset_prefix):
        return normalized[len(problemset_prefix) :].strip("/") or None
    return None


def extract_samples(html: str) -> tuple[tuple[str, str], ...]:
    parser = _SamplesParser()
    parser.feed(html)
    return tuple(parser.samples)


def extract_problem_summaries(html: str, contest_id: str) -> tuple[ProblemSummary, ...]:
    parser = _ProblemListParser(contest_id)
    parser.feed(html)
    return parser.finalize()


def extract_contest_title(html: str, contest_id: str) -> str:
    title = extract_html_title(html, strip_suffix=" - Codeforces")
    if title:
        return title
    return f"Codeforces Contest {contest_id}"


@dataclass(frozen=True)
class CodeforcesProvider:
    provider_name: str = "codeforces"
    hosts: tuple[str, ...] = ("codeforces.com", "www.codeforces.com")
    contest_id_pattern: str = r"^/(?:contest|problemset/problem)/(\d+)(?:/|$)"
    capabilities: ProviderCapabilities = ProviderCapabilities(
        workspace_kind=ProviderWorkspaceKind.CONTEST,
        supports_submission=True,
        requires_credentials=True,
    )

    def _fetch_text(self, url: str) -> str:
        return fetch_text(url)

    def _contest_url(self, contest_id: str) -> str:
        return f"{CODEFORCES_BASE_URL}/contest/{contest_id}"

    def load_problem_samples(self, contest_id: str, problem_id: str) -> tuple[TestCase, ...]:
        url = f"{self._contest_url(contest_id)}/problem/{problem_id}"
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
        html = self._fetch_text(self._contest_url(contest_id))
        return extract_contest_title(html, contest_id)

    def _load_problems_with_progress(
        self,
        contest_id: str,
        problem_summaries: tuple[ProblemSummary, ...],
        progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> tuple[ContestProblem, ...]:
        def build_problem(position: int) -> ContestProblem:
            summary = problem_summaries[position]
            samples = self.load_problem_samples(contest_id, summary.index)
            return ContestProblem(index=summary.index, title=summary.title, samples=samples)

        return load_items_in_parallel(  # type: ignore[return-value]
            problem_summaries,
            build_problem,
            label_fn=lambda i: problem_summaries[i].index,
            progress=progress,
        )

    def _load_problems_by_probe(self, contest_id: str) -> tuple[ContestProblem, ...]:
        problems = []
        for problem_id in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            samples = self.load_problem_samples(contest_id, problem_id)
            if not samples:
                break
            problems.append(ContestProblem(index=problem_id, title=problem_id, samples=samples))
        return tuple(problems)

    def load_contest(
        self,
        contest_id: str,
        *,
        progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> ContestDescriptor:
        contest_html = self._fetch_text(self._contest_url(contest_id))
        title = extract_contest_title(contest_html, contest_id)
        problem_summaries = extract_problem_summaries(contest_html, contest_id)
        if problem_summaries:
            problems = self._load_problems_with_progress(contest_id, problem_summaries, progress=progress)
        else:
            problems = self._load_problems_by_probe(contest_id)
        return ContestDescriptor(
            contest_id=str(contest_id),
            title=title,
            provider=self.provider_name,
            problems=problems,
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
            raise ModuleNotFoundError(translate("error.requests_required_for_codeforces"))
        session = requests.Session()
        login_codeforces(
            session,
            {"username": credentials.username, "password": credentials.secret},
        )
        submit_codeforces(
            session,
            credentials.username,
            str(contest_id),
            str(problem_id),
            int(language_id),
            code,
        )
