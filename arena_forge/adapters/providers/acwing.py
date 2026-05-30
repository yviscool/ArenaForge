from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import List, Optional
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
ACWING_BASE_URL = "https://www.acwing.com"
ACWING_INPUT_HEADING = "\u8f93\u5165\u6837\u4f8b"
ACWING_OUTPUT_HEADING = "\u8f93\u51fa\u6837\u4f8b"


class _AcWingSamplesParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.samples: List[tuple[str, str]] = []
        self._heading_chunks: List[str] = []
        self._current_input = ""
        self._current_side: Optional[str] = None
        self._in_heading = False
        self._in_pre = False
        self._pre_chunks: List[str] = []

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
        self.handle_starttag(tag, attrs)

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
            if "Sample Input" in heading or ACWING_INPUT_HEADING in heading:
                self._current_side = "input"
            elif "Sample Output" in heading or ACWING_OUTPUT_HEADING in heading:
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


def extract_acwing_title(html: str, problem_id: str) -> str:
    match = re.search(r"<title>\s*(.*?)\s*-?\s*AcWing\s*</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if match:
        title = unescape(match.group(1)).strip()
        if title:
            return title
    return f"AcWing Problem {problem_id}"


def extract_acwing_samples(html: str) -> tuple[tuple[str, str], ...]:
    parser = _AcWingSamplesParser()
    parser.feed(html)
    return tuple(parser.samples)


@dataclass(frozen=True)
class AcWingProvider:
    provider_name: str = "acwing"
    capabilities: ProviderCapabilities = ProviderCapabilities(
        workspace_kind=ProviderWorkspaceKind.PROBLEM,
        supports_submission=False,
        requires_credentials=False,
    )

    def _problem_url(self, problem_id: str) -> str:
        return f"{ACWING_BASE_URL}/problem/content/description/{problem_id}/"

    def _fetch_text(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8", "replace")

    def load_contest(self, contest_id: str) -> ContestDescriptor:
        html = self._fetch_text(self._problem_url(contest_id))
        title = extract_acwing_title(html, contest_id)
        samples = extract_acwing_samples(html)
        problem = ContestProblem(
            index=str(contest_id),
            title=title,
            samples=tuple(
                TestCase(
                    name=f"{contest_id}-{index}",
                    input_text=input_text,
                    accepted_outputs=(output_text,),
                )
                for index, (input_text, output_text) in enumerate(samples, start=1)
            ),
        )
        return ContestDescriptor(
            contest_id=str(contest_id),
            title=title,
            provider=self.provider_name,
            problems=(problem,),
        )

    def submit_solution(
        self,
        contest_id: str,
        problem_id: str,
        language_id: int,
        code: str,
        credentials: CredentialRecord,
    ) -> None:
        raise NotImplementedError("AcWing submission is not implemented")
