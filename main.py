from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

if __package__ in {None, ""}:
    # Allow running as a script: `python main.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.assemble import AssembleConfig, write_composite_markdown
from pipeline.normalize import normalize_all
from pipeline.package import PackageConfig, package_with_pandoc
from sources.local_fs import LocalFsConfig, gather_local_fs_sources
from sources.web_scraper import WebConfig, gather_web_sources
from domain import SourceItem


def _load_yaml(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping at root of config: {path}")
    return data


def _gather_sources(cfg: Dict[str, Any], *, base_dir: Path) -> List[SourceItem]:
    sources_cfg = cfg.get("sources") or {}
    if not isinstance(sources_cfg, dict):
        raise ValueError("config.yaml: 'sources' must be a mapping")

    gathered: List[SourceItem] = []

    local_cfg = sources_cfg.get("local_fs") or {}
    if isinstance(local_cfg, dict) and local_cfg.get("enabled", False):
        lcfg = LocalFsConfig(
            roots=local_cfg.get("roots") or ["./"],
            globs=local_cfg.get("globs") or [],
            exclude_globs=local_cfg.get("exclude_globs") or [],
        )
        gathered.extend(gather_local_fs_sources(lcfg, base_dir=base_dir))

    web_cfg = sources_cfg.get("web") or {}
    if isinstance(web_cfg, dict) and web_cfg.get("enabled", False):
        wcfg = WebConfig(
            urls=web_cfg.get("urls") or [],
            content_selector=web_cfg.get("content_selector"),
            container_selector=web_cfg.get("container_selector"),
            paragraph_selector=web_cfg.get("paragraph_selector"),
            exclusion_selector=web_cfg.get("exclusion_selector"),
        )
        gathered.extend(gather_web_sources(wcfg))

    return gathered


def run(config_path: Path) -> Path:
    base_dir = Path.cwd()
    cfg = _load_yaml(config_path)

    output_cfg = cfg.get("output") or {}
    if not isinstance(output_cfg, dict):
        raise ValueError("config.yaml: 'output' must be a mapping")

    out_md = output_cfg.get("composite_markdown_path") or "./out/aggregate.md"
    assemble_cfg = AssembleConfig(output_path=out_md)

    packaging_cfg_raw = output_cfg.get("packaging") or {}
    if not isinstance(packaging_cfg_raw, dict):
        raise ValueError("config.yaml: 'output.packaging' must be a mapping if present")
    packaging_cfg = PackageConfig(
        enabled=packaging_cfg_raw.get("enabled", True),
        epub_path=packaging_cfg_raw.get("epub_path", "./out/book.epub"),
        mobi_path=packaging_cfg_raw.get("mobi_path"),
        title=packaging_cfg_raw.get("title"),
        author=packaging_cfg_raw.get("author"),
        language=packaging_cfg_raw.get("language"),
        metadata_file=packaging_cfg_raw.get("metadata_file"),
        css_file=packaging_cfg_raw.get("css_file"),
    )

    sources = _gather_sources(cfg, base_dir=base_dir)
    normalized = normalize_all(sources)
    md_path = write_composite_markdown(assemble_cfg, normalized, base_dir=base_dir)

    try:
        epub_path, mobi_path = package_with_pandoc(
            input_markdown=md_path,
            base_dir=base_dir,
            cfg=packaging_cfg,
        )
    except RuntimeError as e:
        # Allow running without pandoc installed; caller can inspect logs.
        print(f"[package] Skipping ebook packaging: {e}")
        epub_path = md_path
        mobi_path = None

    return epub_path


def _default_config_path() -> Path:
    """
    Prefer local `config.yaml` (gitignored) when present.
    Fall back to committed `config.example.yaml`.
    """
    script_dir = Path(__file__).resolve().parent
    local_cfg = script_dir / "config.yaml"
    example_cfg = script_dir / "config.example.yaml"
    return local_cfg if local_cfg.exists() else example_cfg


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate sources into one Markdown file.")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config.yaml (defaults to local config.yaml if present; otherwise config.example.yaml)",
    )
    args = parser.parse_args()
    config_path = Path(args.config) if args.config else _default_config_path()
    out_path = run(config_path)
    print(str(out_path))


if __name__ == "__main__":
    main()

