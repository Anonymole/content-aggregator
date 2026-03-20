from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence

from domain import NormalizedItem


@dataclass(frozen=True)
class AssembleConfig:
    output_path: str
    title: str = "Aggregate"
    include_timestamp: bool = True


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def assemble_markdown(items: Sequence[NormalizedItem], *, title: str, include_timestamp: bool) -> str:
    parts: List[str] = []
    parts.append(f"# {title}\n")
    if include_timestamp:
        parts.append(f"_Generated: {_now_utc_iso()}_\n\n")

    for item in items:
        parts.append(f"## {item.title}\n")
        parts.append(f"_Source_: {item.origin}\n\n")
        parts.append(item.markdown.rstrip() + "\n")
        parts.append("\n---\n\n")

    return "".join(parts).rstrip() + "\n"


def write_composite_markdown(cfg: AssembleConfig, items: Iterable[NormalizedItem], *, base_dir: Path) -> Path:
    out_path = Path(cfg.output_path)
    out_path = (base_dir / out_path).resolve() if not out_path.is_absolute() else out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    materialized = list(items)
    content = assemble_markdown(materialized, title=cfg.title, include_timestamp=cfg.include_timestamp)
    out_path.write_text(content, encoding="utf-8")
    return out_path

