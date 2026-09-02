import re
from datetime import date
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

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
