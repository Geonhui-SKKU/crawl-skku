from datetime import date
from urllib.parse import parse_qs, urlsplit

from bs4 import Tag

from crawl_skku.article import utils
from crawl_skku.article.schemas import ArticleAttachment, SkkuArticleKey
from crawl_skku.exceptions import SkkuParseError


def require_tag(root: Tag, selector: str) -> Tag:
    tag = root.select_one(selector)
    if tag is None:
        raise SkkuParseError(f"Missing upstream notice element: {selector}")
    return tag


def require_text(tag: Tag | None) -> str:
    value = utils.tag_text(tag)
    if not value:
        raise SkkuParseError("Missing upstream notice text")
    return value


def post_href(link: Tag) -> str:
    href = link.get("href")
    if not isinstance(href, str) or not href.strip():
        raise SkkuParseError("Missing upstream notice link")
    return href


def query_key(href: str, param: str) -> SkkuArticleKey:
    try:
        value = parse_qs(urlsplit(href).query)[param][0]
        return SkkuArticleKey(type="skku_article", article_no=int(value))
    except (KeyError, ValueError) as exc:
        raise SkkuParseError("Invalid upstream notice identifier") from exc


def post_date(value: str) -> date:
    try:
        return utils.parse_date(value)
    except ValueError as exc:
        raise SkkuParseError("Invalid upstream notice date") from exc


def make_attachment(name: str, href: str, page_url: str) -> ArticleAttachment:
    url = utils.absolute_url(page_url, href)
    return ArticleAttachment(
        name=name, url=url, file_format=utils.extract_file_format(name, url)
    )
