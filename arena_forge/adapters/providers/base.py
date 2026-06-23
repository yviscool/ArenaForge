from __future__ import annotations

from html import unescape
from urllib.request import Request, urlopen

USER_AGENT = "ArenaForge/3.0 (+https://example.invalid)"


def fetch_text(url: str, timeout: int = 10) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def extract_html_title(html: str, strip_suffix: str = "", strip_prefix: str = "") -> str:
    opening = "<title>"
    closing = "</title>"
    start = html.find(opening)
    end = html.find(closing, start + len(opening))
    if start != -1 and end != -1:
        title = unescape(html[start + len(opening) : end]).strip()
        if strip_prefix and title.startswith(strip_prefix):
            title = title[len(strip_prefix) :]
        if strip_suffix:
            title = title.replace(strip_suffix, "")
        title = title.strip()
        if title:
            return title
    return ""
