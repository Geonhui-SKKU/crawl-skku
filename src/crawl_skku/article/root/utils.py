from datetime import date
from pathlib import PurePosixPath
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, Tag

from crawl_skku.article import utils as article_utils
from crawl_skku.article.root import constants
from crawl_skku.article.schemas import (
    ArticleAttachment,
    SkkuArticleKey,
    SkkuArticlePostDetail,
    SkkuArticlePostListItem,
)
from crawl_skku.exceptions import SkkuParseError


def parse_post_list(html: str) -> list[SkkuArticlePostListItem]:
    soup = BeautifulSoup(html, "html.parser")
    list_container = soup.select_one(".board-list-wrap")
    if list_container is None:
        raise SkkuParseError("Could not find SKKU root post list")

    items: list[SkkuArticlePostListItem] = []
    for row in list_container.find_all("li", recursive=False):
        item = _parse_list_row(row)
        if item is not None:
            items.append(item)

    if not items and list_container.find_all("li", recursive=False):
        raise SkkuParseError("Could not parse any SKKU root post rows")

    return items


def parse_post_detail(html: str, article_no: int) -> SkkuArticlePostDetail:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.board_view")
    if table is None:
        raise SkkuParseError("Could not find SKKU root post detail")

    header = table.select_one("thead th")
    if header is None:
        raise SkkuParseError("Could not find SKKU root post header")

    title_tag = header.select_one("em.ellipsis") or header.select_one("em")
    date_tag = header.select_one(".date")
    if title_tag is None or date_tag is None:
        raise SkkuParseError("Could not parse SKKU root post title/date")

    category = article_utils.strip_brackets(_tag_text(header.select_one(".category")))
    title = article_utils.normalize_whitespace(title_tag.get_text(" ", strip=True))
    post_date = _parse_required_date(date_tag.get_text(" ", strip=True))
    author = _parse_detail_author(table)
    attachments = _parse_attachments(table)
    description = _parse_description(table)

    return SkkuArticlePostDetail(
        key=SkkuArticleKey(type="skku_article", article_no=article_no),
        category=category,
        title=title,
        date=post_date,
        author=author,
        url=constants.build_detail_url(article_no),
        has_attachment=bool(attachments),
        description=description,
        attachments=attachments or None,
    )


def _parse_list_row(row: Tag) -> SkkuArticlePostListItem | None:
    title_link = row.select_one(".board-list-content-title a[href*='articleNo']")
    if title_link is None:
        return None

    href = title_link.get("href")
    if not isinstance(href, str):
        return None

    article_no = _parse_article_no(href)
    if article_no is None:
        return None

    title = article_utils.normalize_whitespace(title_link.get_text(" ", strip=True))
    if not title:
        return None

    category = article_utils.strip_brackets(
        _tag_text(row.select_one(".c-board-list-category"))
    )
    info_texts = _parse_list_info_texts(row)
    post_date, date_index = _parse_date_from_info(info_texts)
    author = _parse_list_author(info_texts, date_index)

    return SkkuArticlePostListItem(
        key=SkkuArticleKey(type="skku_article", article_no=article_no),
        category=category,
        title=title,
        date=post_date,
        author=author,
        url=article_utils.absolute_url(constants.BOARD_BASE_URL, href),
        has_attachment=_row_has_attachment(row),
    )


def _parse_article_no(href: str) -> int | None:
    values = parse_qs(urlparse(href).query).get("articleNo")
    if not values:
        return None

    try:
        return int(values[0])
    except ValueError:
        return None


def _parse_list_info_texts(row: Tag) -> list[str]:
    info = row.select_one(".board-list-content-info ul")
    if info is None:
        return []

    return [
        article_utils.normalize_whitespace(li.get_text(" ", strip=True))
        for li in info.find_all("li", recursive=False)
    ]


def _parse_date_from_info(info_texts: list[str]) -> tuple[date, int]:
    for index, text in enumerate(info_texts):
        try:
            return article_utils.parse_date(text), index
        except ValueError:
            continue

    raise SkkuParseError("Could not parse SKKU root post list date")


def _parse_list_author(info_texts: list[str], date_index: int) -> str | None:
    if date_index <= 0:
        return None

    author = info_texts[date_index - 1]
    if not author or author.startswith("No."):
        return None

    return author


def _row_has_attachment(row: Tag) -> bool:
    attachment_wrap = row.select_one(".board-list-etc-wrap")
    if attachment_wrap is None:
        return False

    return bool(
        attachment_wrap.select_one(
            (
                "a[href*='download'], "
                "img[alt*='첨부'], "
                "img[src*='file'], "
                ".file, "
                ".c-board-file-icon, "
                ".board-list-file"
            ),
        ),
    )


def _parse_detail_author(table: Tag) -> str | None:
    author_tag = table.select_one(".boardView_txtWrap .flL .boardView_txtList li")
    author = _tag_text(author_tag)
    return author or None


def _parse_attachments(table: Tag) -> list[ArticleAttachment]:
    attachments: list[ArticleAttachment] = []
    for link in table.select(".filedown_list a[href*='mode=download']"):
        href = link.get("href")
        if not isinstance(href, str):
            continue

        name = article_utils.normalize_whitespace(link.get_text(" ", strip=True))
        if not name:
            continue

        url = article_utils.absolute_url(constants.BOARD_BASE_URL, href)
        attachments.append(
            ArticleAttachment(
                file_format=article_utils.extract_file_format(name, url),
                name=name,
                url=url,
            ),
        )

    content = _find_description_content(table)
    if content is not None:
        seen_urls = {attachment.url for attachment in attachments}
        attachments.extend(_parse_inline_image_attachments(content, seen_urls))

    return attachments


def _parse_description(table: Tag) -> str:
    content = _find_description_content(table)
    if content is None:
        raise SkkuParseError("Could not find SKKU root post description")

    for removable in content.select("script, style"):
        removable.decompose()

    description = article_utils.normalize_multiline_text(
        content.get_text("\n", strip=True)
    )
    if not description:
        raise SkkuParseError("Could not parse SKKU root post description")

    return description


def _find_description_content(table: Tag) -> Tag | None:
    content = table.select_one(".board-write-box dd")
    if content is None:
        content = table.select_one(".board-write-box")
    return content


def _parse_inline_image_attachments(
    content: Tag, seen_urls: set[str]
) -> list[ArticleAttachment]:
    attachments: list[ArticleAttachment] = []
    for image in content.select("img[src]"):
        src = image.get("src")
        if not isinstance(src, str):
            continue

        src = src.strip()
        if not src or src.startswith(("data:", "blob:")):
            continue

        url = article_utils.absolute_url(constants.BOARD_BASE_URL, src)
        if url in seen_urls:
            continue

        name = _inline_image_name(image, url, len(attachments) + 1)
        file_format = article_utils.extract_file_format(name, url)
        if file_format != "unknown" and not PurePosixPath(name).suffix:
            name = f"{name}.{file_format}"

        attachments.append(
            ArticleAttachment(
                file_format=file_format,
                name=name,
                url=url,
            ),
        )
        seen_urls.add(url)

    return attachments


def _inline_image_name(image: Tag, url: str, index: int) -> str:
    for attr in ("alt", "title"):
        value = image.get(attr)
        if isinstance(value, str):
            name = article_utils.normalize_whitespace(value)
            if name:
                return name

    filename = article_utils.normalize_whitespace(
        urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    )
    return filename or f"inline-image-{index}"


def _parse_required_date(value: str) -> date:
    try:
        return article_utils.parse_date(value)
    except ValueError as exc:
        raise SkkuParseError("Could not parse SKKU root post date") from exc


def _tag_text(tag: Tag | None) -> str:
    if tag is None:
        return ""
    return article_utils.normalize_whitespace(tag.get_text(" ", strip=True))
