from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from time import sleep
from typing import Callable, Dict, Optional, Tuple
from urllib.request import Request, urlopen

USER_AGENT = "ArenaForge/3.0 (+https://example.invalid)"
_FETCH_MAX_RETRIES = 2
_FETCH_BACKOFF_BASE = 1.0


def fetch_text(url: str, timeout: int = 10) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Optional[OSError] = None
    for attempt in range(_FETCH_MAX_RETRIES + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", "replace")
        except OSError as exc:
            last_error = exc
            if attempt < _FETCH_MAX_RETRIES:
                sleep(_FETCH_BACKOFF_BASE * (2 ** attempt))
    raise last_error  # type: ignore[misc]


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


def load_items_in_parallel(
    items: tuple,
    load_fn: Callable[[int], object],
    *,
    label_fn: Callable[[int], str] = lambda i: str(i),
    progress: Optional[Callable[[int, int, str], None]] = None,
    max_workers: int = 8,
) -> Tuple[object, ...]:
    total = len(items)
    if total == 0:
        return ()
    results: Dict[int, object] = {}
    workers = min(max_workers, total)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(load_fn, position): position
            for position in range(total)
        }
        completed = 0
        for future in as_completed(futures):
            position = futures[future]
            results[position] = future.result()
            completed += 1
            if progress is not None:
                progress(completed, total, label_fn(position))
    return tuple(results[position] for position in range(total))
