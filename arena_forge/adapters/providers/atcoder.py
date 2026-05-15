from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Callable, Dict, List, Optional
from urllib.parse import urljoin
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
ATCODER_BASE_URL = "https://atcoder.jp"


@dataclass(frozen=True)
class TaskSummary:
    index: str
    title: str
    url: str


@dataclass
class _MutableTaskSummary:
    url: str
    index: Optional[str] = None
    title: Optional[str] = None


class _TaskListParser(HTMLParser):
    def __init__(self, contest_id: str) -> None:
        super().__init__(convert_charrefs=False)
        self.contest_id = contest_id
        self._tasks: Dict[str, _MutableTaskSummary] = {}
        self._order: List[str] = []
        self._active_href: Optional[str] = None
        self._active_chunks: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        if href.startswith(f"/contests/{self.contest_id}/tasks/"):
            self._active_href = href
            self._active_chunks = []

    def handle_data(self, data: str) -> None:
        if self._active_href is not None:
            self._active_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._active_href is None:
            return
        text = " ".join(unescape("".join(self._active_chunks)).split())
        href = self._active_href
        self._active_href = None
        self._active_chunks = []
        if not text:
            return
        if href not in self._tasks:
            self._tasks[href] = _MutableTaskSummary(url=urljoin(ATCODER_BASE_URL, href))
            self._order.append(href)
        task = self._tasks[href]
        if _looks_like_problem_index(text) and task.index is None:
            task.index = text
        elif task.title is None:
            task.title = text

    def finalize(self) -> tuple[TaskSummary, ...]:
        tasks: List[TaskSummary] = []
        for href in self._order:
            task = self._tasks[href]
            slug = href.rstrip("/").rsplit("/", 1)[-1]
            index = task.index or _index_from_task_slug(slug)
            title = task.title or index
            tasks.append(TaskSummary(index=index, title=title, url=task.url))
        return tuple(tasks)


class _SamplesParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.samples: List[tuple[str, str]] = []
        self._heading_chunks: List[str] = []
        self._pre_chunks: List[str] = []
        self._current_input = ""
        self._current_side: Optional[str] = None
        self._in_heading = False
        self._in_pre = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"h3", "h4"}:
            self._in_heading = True
            self._heading_chunks = []
        elif tag == "pre" and self._current_side is not None:
            self._in_pre = True
            self._pre_chunks = []
        elif tag == "br" and self._in_pre:
            self._pre_chunks.append("\n")

    def handle_startendtag(self, tag: str, attrs) -> None:
        if tag == "br" and self._in_pre:
            self._pre_chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._heading_chunks.append(data)
        elif self._in_pre:
            self._pre_chunks.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._in_pre:
            self._pre_chunks.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._in_pre:
            self._pre_chunks.append(f"&#{name};")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h3", "h4"} and self._in_heading:
            heading = " ".join(unescape("".join(self._heading_chunks)).split())
            if heading.startswith("Sample Input"):
                self._current_side = "input"
            elif heading.startswith("Sample Output"):
                self._current_side = "output"
            else:
                self._current_side = None
            self._heading_chunks = []
            self._in_heading = False
            return
        if tag == "pre" and self._in_pre:
            text = unescape("".join(self._pre_chunks)).replace("\r\n", "\n").strip()
            if self._current_side == "input":
                self._current_input = text
            elif self._current_side == "output":
                self.samples.append((self._current_input, text))
            self._pre_chunks = []
            self._in_pre = False


class _PrintTasksParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._problems: List[ContestProblem] = []
        self._current_index: Optional[str] = None
        self._current_title: Optional[str] = None
        self._current_samples: List[tuple[str, str]] = []
        self._current_input = ""
        self._current_side: Optional[str] = None
        self._english_depth = 0
        self._in_heading = False
        self._heading_chunks: List[str] = []
        self._in_pre = False
        self._pre_chunks: List[str] = []
        self._in_task_heading = False
        self._task_heading_chunks: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_map = {key: value or "" for key, value in attrs}
        class_name = attrs_map.get("class", "")
        if tag == "span" and "h2" in class_name.split():
            self._finalize_problem()
            self._in_task_heading = True
            self._task_heading_chunks = []
            return
        if tag == "span" and "lang-en" in class_name.split():
            self._english_depth = 1
            return
        if self._english_depth == 0:
            return
        self._english_depth += 1
        if tag in {"h3", "h4"}:
            self._in_heading = True
            self._heading_chunks = []
        elif tag == "pre" and self._current_side is not None:
            self._in_pre = True
            self._pre_chunks = []
        elif tag == "br" and self._in_pre:
            self._pre_chunks.append("\n")

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self._in_task_heading:
            self._task_heading_chunks.append(data)
        elif self._in_heading:
            self._heading_chunks.append(data)
        elif self._in_pre:
            self._pre_chunks.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._in_pre:
            self._pre_chunks.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._in_pre:
            self._pre_chunks.append(f"&#{name};")

    def handle_endtag(self, tag: str) -> None:
        if self._in_task_heading and tag == "span":
            heading = " ".join(unescape("".join(self._task_heading_chunks)).split())
            index, separator, title = heading.partition(" - ")
            self._current_index = index.strip() or None
            self._current_title = title.strip() if separator and title.strip() else (self._current_index or None)
            self._task_heading_chunks = []
            self._in_task_heading = False
            return
        if self._english_depth == 0:
            return
        if tag in {"h3", "h4"} and self._in_heading:
            heading = " ".join(unescape("".join(self._heading_chunks)).split())
            if heading.startswith("Sample Input"):
                self._current_side = "input"
            elif heading.startswith("Sample Output"):
                self._current_side = "output"
            else:
                self._current_side = None
            self._heading_chunks = []
            self._in_heading = False
        elif tag == "pre" and self._in_pre:
            text = unescape("".join(self._pre_chunks)).replace("\r\n", "\n").strip()
            if self._current_side == "input":
                self._current_input = text
            elif self._current_side == "output":
                self._current_samples.append((self._current_input, text))
            self._pre_chunks = []
            self._in_pre = False
        self._english_depth -= 1

    def finalize(self) -> tuple[ContestProblem, ...]:
        self._finalize_problem()
        return tuple(self._problems)

    def _finalize_problem(self) -> None:
        if self._current_index is None:
            return
        self._problems.append(
            ContestProblem(
                index=self._current_index,
                title=self._current_title or self._current_index,
                samples=tuple(
                    TestCase(
                        name=f"{self._current_index}-{index + 1}",
                        input_text=input_text,
                        accepted_outputs=(output_text,),
                    )
                    for index, (input_text, output_text) in enumerate(self._current_samples)
                ),
            )
        )
        self._current_index = None
        self._current_title = None
        self._current_samples = []
        self._current_input = ""
        self._current_side = None


def _looks_like_problem_index(value: str) -> bool:
    if value == "Ex":
        return True
    return value.isalnum() and value.upper() == value and " " not in value and len(value) <= 4


def _index_from_task_slug(slug: str) -> str:
    suffix = slug.rsplit("_", 1)[-1]
    if suffix == "ex":
        return "Ex"
    return suffix.upper()


def extract_task_summaries(html: str, contest_id: str) -> tuple[TaskSummary, ...]:
    parser = _TaskListParser(contest_id)
    parser.feed(html)
    return parser.finalize()


def extract_atcoder_samples(html: str) -> tuple[tuple[str, str], ...]:
    parser = _SamplesParser()
    parser.feed(html)
    return tuple(parser.samples)


def extract_printed_tasks(html: str) -> tuple[ContestProblem, ...]:
    parser = _PrintTasksParser()
    parser.feed(html)
    return parser.finalize()


def extract_atcoder_contest_title(html: str, contest_id: str) -> str:
    opening = "<title>"
    closing = "</title>"
    start = html.find(opening)
    end = html.find(closing, start + len(opening))
    if start != -1 and end != -1:
        title = unescape(html[start + len(opening) : end]).strip()
        if title.startswith("Tasks - "):
            title = title[len("Tasks - ") :]
        title = title.replace(" - AtCoder", "").strip()
        if title:
            return title
    return f"AtCoder Contest {contest_id}"


@dataclass(frozen=True)
class AtCoderProvider:
    provider_name: str = "atcoder"
    capabilities: ProviderCapabilities = ProviderCapabilities(
        workspace_kind=ProviderWorkspaceKind.CONTEST,
        supports_submission=False,
        requires_credentials=False,
    )

    def _fetch_text(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8", "replace")

    def _contest_tasks_url(self, contest_id: str) -> str:
        return f"{ATCODER_BASE_URL}/contests/{contest_id}/tasks?lang=en"

    def _contest_print_url(self, contest_id: str) -> str:
        return f"{ATCODER_BASE_URL}/contests/{contest_id}/tasks_print?lang=en"

    def _task_url(self, contest_id: str, task_id: str) -> str:
        return f"{ATCODER_BASE_URL}/contests/{contest_id}/tasks/{task_id}?lang=en"

    def load_problem_samples(self, contest_id: str, task_id: str, problem_index: str) -> tuple[TestCase, ...]:
        html = self._fetch_text(self._task_url(contest_id, task_id))
        samples = extract_atcoder_samples(html)
        return tuple(
            TestCase(
                name=f"{problem_index}-{index + 1}",
                input_text=input_text,
                accepted_outputs=(output_text,),
            )
            for index, (input_text, output_text) in enumerate(samples)
        )

    def load_contest_title(self, contest_id: str) -> str:
        html = self._fetch_text(self._contest_tasks_url(contest_id))
        return extract_atcoder_contest_title(html, contest_id)

    def _load_problems_from_tasks_page(
        self,
        contest_id: str,
        task_summaries: tuple[TaskSummary, ...],
        progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> tuple[ContestProblem, ...]:
        total = len(task_summaries)
        if total == 0:
            return ()

        def build_problem(summary: TaskSummary) -> ContestProblem:
            task_id = summary.url.rstrip("/").rsplit("/", 1)[-1].split("?", 1)[0]
            return ContestProblem(
                index=summary.index,
                title=summary.title,
                samples=self.load_problem_samples(contest_id, task_id, summary.index),
            )

        results: Dict[int, ContestProblem] = {}
        max_workers = min(8, total)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(build_problem, summary): (position, summary)
                for position, summary in enumerate(task_summaries)
            }
            completed = 0
            for future in as_completed(futures):
                position, summary = futures[future]
                results[position] = future.result()
                completed += 1
                if progress is not None:
                    progress(completed, total, summary.index)
        return tuple(results[position] for position in range(total))

    def load_contest(
        self,
        contest_id: str,
        *,
        progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> ContestDescriptor:
        title = f"AtCoder Contest {contest_id}"
        printed_problems = ()
        try:
            print_html = self._fetch_text(self._contest_print_url(contest_id))
        except Exception:
            print_html = None
        if print_html is not None:
            title = extract_atcoder_contest_title(print_html, contest_id)
            printed_problems = extract_printed_tasks(print_html)
        if printed_problems:
            problems = printed_problems
        else:
            tasks_html = self._fetch_text(self._contest_tasks_url(contest_id))
            title = extract_atcoder_contest_title(tasks_html, contest_id)
            task_summaries = extract_task_summaries(tasks_html, contest_id)
            problems = self._load_problems_from_tasks_page(contest_id, task_summaries, progress=progress)
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
        raise NotImplementedError("AtCoder submission is not implemented")
