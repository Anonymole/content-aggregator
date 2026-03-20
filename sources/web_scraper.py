from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterator, Optional, Sequence

import requests
from bs4 import BeautifulSoup

from domain import SourceItem


@dataclass(frozen=True)
class WebConfig:
    urls: Sequence[str]
    # Legacy: a single selector used directly on the whole document
    content_selector: Optional[str] = None
    # Preferred for structured extraction:
    # - container_selector: outer wrapper for main article content
    # - paragraph_selector: repeated blocks within that wrapper
    # - exclusion_selector: first element that marks the start of comments
    #   (everything at or after this element is ignored)
    container_selector: Optional[str] = None
    paragraph_selector: Optional[str] = None
    exclusion_selector: Optional[str] = None
    timeout_s: float = 30.0
    user_agent: str = "aggregator/0.1 (+https://local)"


def _stable_id(prefix: str, value: str) -> str:
    h = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{h}"


def _extract_title(soup: BeautifulSoup, url: str) -> str:
    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(strip=True)
    return url


def _extract_html_fragment(soup: BeautifulSoup, selector: Optional[str]) -> str:
    if selector:
        el = soup.select_one(selector)
        if el is not None:
            return str(el)
    return str(soup.body or soup)


def _extract_structured_html(
    soup: BeautifulSoup,
    container_selector: Optional[str],
    paragraph_selector: Optional[str],
    legacy_selector: Optional[str],
    exclusion_selector: Optional[str],
) -> str:
    # 1) Use explicit container + paragraph model if provided
    if container_selector:
        container = soup.select_one(container_selector)
        if container is not None:
            # If we have an exclusion marker, walk descendants in order and
            # collect paragraphs until we hit the first exclusion node.
            if paragraph_selector and exclusion_selector:
                exclusion_node = container.select_one(exclusion_selector)
                if exclusion_node is not None:
                    parts: list[str] = []
                    for node in container.descendants:
                        if node is exclusion_node:
                            break
                        if (
                            getattr(node, "name", None) == "p"
                            and node.has_attr("class")
                            and "wp-block-paragraph" in node["class"]
                        ):
                            parts.append(str(node))
                    if parts:
                        return "".join(parts)

            if paragraph_selector:
                paras = container.select(paragraph_selector)
                if paras:
                    # Concatenate paragraph HTML fragments in order.
                    return "".join(str(p) for p in paras)

            # Fallback: full container HTML
            return str(container)

    # 2) Fall back to the legacy single selector if configured
    if legacy_selector:
        return _extract_html_fragment(soup, legacy_selector)

    # 3) Final fallback: whole body
    return _extract_html_fragment(soup, None)


def iter_web_sources(cfg: WebConfig) -> Iterator[SourceItem]:
    headers = {"User-Agent": cfg.user_agent}
    session = requests.Session()

    for url in cfg.urls:
        resp = session.get(url, headers=headers, timeout=cfg.timeout_s)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "").split(";")[0].strip().lower() or None
        text = resp.text

        if content_type in {"text/markdown", "text/plain"} or url.lower().endswith((".md", ".markdown", ".txt")):
            title = url
            content = text
            ct = content_type or "text/plain"
        else:
            soup = BeautifulSoup(text, "html.parser")
            title = _extract_title(soup, url)
            content = _extract_structured_html(
                soup,
                container_selector=cfg.container_selector,
                paragraph_selector=cfg.paragraph_selector,
                legacy_selector=cfg.content_selector,
                exclusion_selector=cfg.exclusion_selector,
            )
            ct = content_type or "text/html"

        yield SourceItem(
            kind="web",
            source_id=_stable_id("web", url),
            title=title,
            origin=url,
            content=content,
            content_type=ct,
        )


def gather_web_sources(cfg: WebConfig) -> list[SourceItem]:
    return list(iter_web_sources(cfg))

