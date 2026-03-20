from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from domain import SourceItem


@dataclass(frozen=True)
class LocalFsConfig:
    roots: Sequence[str]
    globs: Sequence[str]
    exclude_globs: Sequence[str] = ()


def _stable_id(prefix: str, value: str) -> str:
    h = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{h}"


def iter_local_fs_sources(cfg: LocalFsConfig, *, base_dir: Path) -> Iterator[SourceItem]:
    roots = [Path(r) for r in cfg.roots]
    root_paths = [(base_dir / r).resolve() if not r.is_absolute() else r.resolve() for r in roots]

    exclude: set[Path] = set()
    for root in root_paths:
        for pat in cfg.exclude_globs:
            for p in root.glob(pat):
                exclude.add(p.resolve())

    seen: set[Path] = set()
    for root in root_paths:
        for pat in cfg.globs:
            for path in root.glob(pat):
                p = path.resolve()
                if p in seen or p in exclude:
                    continue
                if p.is_dir():
                    continue
                seen.add(p)

                try:
                    text = p.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = p.read_text(encoding="utf-8", errors="replace")

                origin = str(p)
                title = p.name
                yield SourceItem(
                    kind="local_fs",
                    source_id=_stable_id("local_fs", origin),
                    title=title,
                    origin=origin,
                    content=text,
                    content_type="text/plain",
                )


def gather_local_fs_sources(cfg: LocalFsConfig, *, base_dir: Path) -> list[SourceItem]:
    return list(iter_local_fs_sources(cfg, base_dir=base_dir))

