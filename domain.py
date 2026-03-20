from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


SourceKind = Literal["local_fs", "web"]


@dataclass(frozen=True)
class SourceItem:
    kind: SourceKind
    source_id: str
    title: str
    origin: str
    content: str
    content_type: Optional[str] = None  # e.g. "text/markdown", "text/html"


@dataclass(frozen=True)
class NormalizedItem:
    kind: SourceKind
    source_id: str
    title: str
    origin: str
    markdown: str

