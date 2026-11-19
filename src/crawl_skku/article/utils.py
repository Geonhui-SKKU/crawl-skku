import re
from datetime import date
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

from bs4 import Tag

from crawl_skku.article.schemas import ArticleAttachment

DATE_RE = re.compile(r"(?P<year>\d{4})[.-](?P<month>\d{1,2})[.-](?P<day>\d{1,2})")


def normalize_whitespace(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.split())


def normalize_multiline_text(value: str | None) -> str:
    if value is None:
        return ""

    lines = [normalize_whitespace(line) for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def strip_brackets(value: str | None) -> str | None:
    normalized = normalize_whitespace(value)
    if not normalized:
        return None
    return normalized.strip("[]") or None


def parse_date(value: str) -> date:
    match = DATE_RE.search(value)
    if match is None:
        raise ValueError(f"Could not parse date from {value!r}")

    return date(
        int(match.group("year")),
        int(match.group("month")),
        int(match.group("day")),
    )


def absolute_url(base_url: str, href: str) -> str:
    return urljoin(base_url, href)


def extract_file_format(name: str, url: str | None = None) -> str:
    suffix = PurePosixPath(name).suffix.lstrip(".").lower()
    if suffix:
        return suffix

    if url:
        path = urlparse(url).path
        suffix = PurePosixPath(path).suffix.lstrip(".").lower()
        if suffix:
            return suffix

    return "unknown"


def tag_text(tag: Tag | None) -> str:
    return normalize_whitespace(tag.get_text(" ", strip=True)) if tag else ""


def parse_body(
    content: Tag, file_links: list[Tag], page_url: str
) -> tuple[str, list[ArticleAttachment]]:
    for removable in content.select("script, style"):
        removable.decompose()

    attachments: list[ArticleAttachment] = []
    seen: set[str] = set()
    for tag in [*file_links, *content.select("img[src]")]:
        is_image = tag.name == "img"
        href = tag.get("src" if is_image else "href")
        if not isinstance(href, str) or not href.strip():
            continue
        url = absolute_url(page_url, href.strip())
        path = urlparse(url)
        if path.scheme not in {"http", "https"} or url in seen:
            continue
        name = tag_text(tag)
        if is_image:
            name = next(
                (
                    normalize_whitespace(value)
                    for value in (tag.get("alt"), tag.get("title"))
                    if isinstance(value, str) and value.strip()
                ),
                PurePosixPath(path.path).name or f"inline-image-{len(attachments) + 1}",
            )
        if not name:
            continue
        seen.add(url)
        attachments.append(
            ArticleAttachment(
                name=name, url=url, file_format=extract_file_format(name, url)
            )
        )

    return normalize_multiline_text(content.get_text("\n", strip=True)), attachments
