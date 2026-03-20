from __future__ import annotations

import re
from typing import Iterable, List

from markdownify import markdownify as html_to_md

from domain import NormalizedItem, SourceItem


_TRAILING_WS_RE = re.compile(r"[ \t]+$", re.MULTILINE)


def _clean_markdown(md: str) -> str:
    md = md.replace("\r\n", "\n").replace("\r", "\n")
    md = _TRAILING_WS_RE.sub("", md)
    return md.strip() + "\n"


def normalize_item(item: SourceItem) -> NormalizedItem:
    ct = (item.content_type or "").lower()

    if ct.startswith("text/html") or ct == "application/xhtml+xml":
        md = html_to_md(item.content, heading_style="ATX")
    else:
        md = item.content

    md = _clean_markdown(md)
    return NormalizedItem(
        kind=item.kind,
        source_id=item.source_id,
        title=item.title,
        origin=item.origin,
        markdown=md,
    )


def normalize_all(items: Iterable[SourceItem]) -> List[NormalizedItem]:
    return [normalize_item(i) for i in items]

