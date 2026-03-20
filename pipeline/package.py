from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Optional


@dataclass(frozen=True)
class PackageConfig:
    enabled: bool = True
    epub_path: str = "./out/book.epub"
    mobi_path: Optional[str] = None  # if set, try Calibre's `ebook-convert`
    title: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None  # e.g. "en"
    metadata_file: Optional[str] = None
    css_file: Optional[str] = None


def _ensure_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required binary '{name}' was not found on PATH.")
    return path


def package_with_pandoc(
    *,
    input_markdown: Path,
    base_dir: Path,
    cfg: PackageConfig,
) -> tuple[Path, Optional[Path]]:
    """
    Produce EPUB (and optionally MOBI) from a composite Markdown file.
    Returns (epub_path, mobi_path_or_None).
    """
    if not cfg.enabled:
        return (input_markdown, None)

    pandoc_bin = _ensure_binary("pandoc")

    epub_path = Path(cfg.epub_path)
    epub_path = (base_dir / epub_path).resolve() if not epub_path.is_absolute() else epub_path.resolve()
    epub_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [pandoc_bin, str(input_markdown), "-o", str(epub_path)]

    if cfg.title:
        cmd.extend(["--metadata", f"title={cfg.title}"])
    if cfg.author:
        cmd.extend(["--metadata", f"author={cfg.author}"])
    if cfg.language:
        cmd.extend(["--metadata", f"lang={cfg.language}"])

    if cfg.metadata_file:
        meta_path = Path(cfg.metadata_file)
        meta_path = (base_dir / meta_path).resolve() if not meta_path.is_absolute() else meta_path.resolve()
        if meta_path.is_file():
            cmd.extend(["--metadata-file", str(meta_path)])

    if cfg.css_file:
        css_path = Path(cfg.css_file)
        css_path = (base_dir / css_path).resolve() if not css_path.is_absolute() else css_path.resolve()
        if css_path.is_file():
            cmd.extend(["--css", str(css_path)])

    subprocess.run(cmd, check=True)

    mobi_out: Optional[Path] = None
    if cfg.mobi_path:
        ebook_convert = shutil.which("ebook-convert")
        if ebook_convert:
            mobi_out = Path(cfg.mobi_path)
            mobi_out = (base_dir / mobi_out).resolve() if not mobi_out.is_absolute() else mobi_out.resolve()
            mobi_out.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([ebook_convert, str(epub_path), str(mobi_out)], check=True)

    return epub_path, mobi_out

