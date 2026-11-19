"""Parser and service for the SKKU CMS notice board templates."""

from collections.abc import Callable
from datetime import date
from typing import Generic
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup

from crawl_skku import service
from crawl_skku.article import utils
from crawl_skku.article.board_service import CachedArticleBoard, PostT
from crawl_skku.article.schemas import (
    ArticlePostKey,
    SkkuArticleKey,
    SkkuArticlePostDetail,
    SkkuArticlePostListItem,
    SkkuIntegratedArticleKey,
    SkkuIntegratedArticlePostDetail,
    SkkuIntegratedArticlePostListItem,
)
from crawl_skku.exceptions import SkkuParseError


def _metadata(values: list[str]) -> tuple[str | None, date]:
    for index, value in enumerate(values):
        try:
            post_date = utils.parse_date(value)
        except ValueError:
            continue
        author = next(
            (
                text
                for text in reversed(values[:index])
                if text and not text.startswith(("No.", "공지", "조회수"))
            ),
            None,
        )
        return author, post_date
    raise SkkuParseError("Could not parse SKKU CMS post date")


def _parse_list(
    html: str,
    url: str,
    offset: int,
    model: type[PostT],
    parse_key: Callable[[dict[str, list[str]]], ArticlePostKey],
) -> tuple[list[PostT], list[PostT]]:
    soup = BeautifulSoup(html, "html.parser")
    board = soup.select_one(".board-list-wrap")
    if board is None:
        raise SkkuParseError("Could not find SKKU CMS post list")
    # Some integrated boards replay the last page for offsets beyond the end.
    last_page = soup.select_one(".paging-wrap .page-last[href]")
    last_href = last_page.get("href") if last_page else None
    past_end = False
    if isinstance(last_href, str):
        last_offset = parse_qs(urlsplit(last_href).query).get("article.offset", [""])[0]
        past_end = last_offset.isdecimal() and offset > int(last_offset)
    pinned: list[PostT] = []
    regular: list[PostT] = []
    for row in board.select(":scope > li"):
        is_pinned = row.select_one(".board-list-content-top") is not None
        if past_end and not is_pinned:
            continue
        link = row.select_one(".board-list-content-title a[href]")
        if link is None:
            if not utils.tag_text(row) or utils.tag_text(row) in {
                "등록된 게시물이 없습니다.",
                "등록된 게시글이 없습니다.",
                "등록된 글이 없습니다.",
                "검색된 게시물이 없습니다.",
            }:
                continue
            raise SkkuParseError("Could not find SKKU CMS post link")
        href = link.get("href")
        title = utils.tag_text(link)
        if not isinstance(href, str) or not title:
            raise SkkuParseError("Invalid SKKU CMS post link or title")
        try:
            key = parse_key(parse_qs(urlsplit(href).query))
        except (KeyError, ValueError) as exc:
            raise SkkuParseError("Invalid SKKU CMS post identifiers") from exc
        author, post_date = _metadata(
            [utils.tag_text(tag) for tag in row.select(".board-list-content-info li")]
        )
        item = model.model_validate(
            {
                "key": key,
                "title": title,
                "category": utils.strip_brackets(
                    utils.tag_text(row.select_one(".c-board-list-category"))
                ),
                "author": author,
                "date": post_date,
                "url": utils.absolute_url(url, href),
                "has_attachment": row.select_one(
                    ".board-list-etc-wrap .c-board-file-icon, "
                    ".board-list-etc-wrap .board-list-file, "
                    ".board-list-etc-wrap .file-down-btn"
                )
                is not None,
            }
        )
        (pinned if is_pinned else regular).append(item)
    return pinned, regular


def _parse_detail(
    html: str, url: str, key: ArticlePostKey, model: type[PostT]
) -> PostT:
    box = BeautifulSoup(html, "html.parser").select_one(".board-view-box")
    if box is None:
        raise SkkuParseError("Could not find SKKU CMS post detail")
    title_tag = box.select_one(".board-view-title-wrap h4")
    content = box.select_one(".board-view-content-wrap")
    if title_tag is None or content is None:
        raise SkkuParseError("Could not find SKKU CMS post title or body")
    category_tag = title_tag.select_one(".c-board-view-category")
    if category_tag is None:
        span = title_tag.select_one(":scope > span:first-child")
        label = utils.tag_text(span)
        if label.startswith("[") and label.endswith("]"):
            category_tag = span
    category = utils.strip_brackets(utils.tag_text(category_tag))
    if category_tag is not None:
        category_tag.decompose()
    title = utils.tag_text(title_tag)
    if not title:
        raise SkkuParseError("Could not parse SKKU CMS post title")
    author, post_date = _metadata(
        [
            utils.tag_text(tag)
            for tag in box.select(".board-view-title-wrap .board-etc-wrap li")
        ]
    )
    description, attachments = utils.parse_body(
        content, box.select(".board-view-file-wrap a[href]"), url
    )
    return model.model_validate(
        {
            "key": key,
            "title": title,
            "category": category,
            "author": author,
            "date": post_date,
            "url": url,
            "description": description,
            "has_attachment": bool(attachments),
            "attachments": attachments or None,
        }
    )


class _CmsBoard(CachedArticleBoard[PostT], Generic[PostT]):
    def __init__(
        self,
        source: str,
        url: str,
        model: type[PostT],
        list_model: type[list[PostT]],
        parse_key: Callable[[dict[str, list[str]]], ArticlePostKey],
    ) -> None:
        super().__init__(source, url, list_model)
        self._model = model
        self._parse_key = parse_key

    async def _load_page(
        self, offset: int, size: int
    ) -> tuple[list[PostT], list[PostT]]:
        html = await service.fetch_html(
            self.url, params={"article.offset": offset, "articleLimit": size}
        )
        return _parse_list(html, self.url, offset, self._model, self._parse_key)

    async def _load_posts(self, offset: int, limit: int) -> list[PostT]:
        # The integrated CMS rounds unaligned offsets down to its page boundary.
        # Numbered boards may prepend the same pinned rows to each upstream page.
        first_offset = offset // limit * limit
        pinned, first_regular = await self._load_page(first_offset, limit)
        result = pinned[offset : offset + limit]
        regular_offset = max(0, offset - len(pinned))
        while len(result) < limit:
            page_offset, start = divmod(regular_offset, limit)
            page_offset *= limit
            if page_offset == first_offset:
                regular = first_regular
            else:
                _, regular = await self._load_page(page_offset, limit)
            result.extend(regular[start : start + limit - len(result)])
            if len(regular) < limit:
                break
            regular_offset = page_offset + limit
        return result


def _numbered_key(query: dict[str, list[str]]) -> SkkuArticleKey:
    return SkkuArticleKey(type="skku_article", article_no=int(query["articleNo"][0]))


def _integrated_key(query: dict[str, list[str]]) -> SkkuIntegratedArticleKey:
    return SkkuIntegratedArticleKey(
        type="skku_article",
        board_id=int(query["viewBoardId"][0]),
        item_id=query["itemId"][0],
    )


class NumberedCmsBoard(_CmsBoard[SkkuArticlePostListItem]):
    def __init__(self, source: str, url: str) -> None:
        super().__init__(
            source,
            url,
            SkkuArticlePostListItem,
            list[SkkuArticlePostListItem],
            _numbered_key,
        )

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail:
        key = SkkuArticleKey(type="skku_article", article_no=article_no)
        return await self._get_detail(
            key={"article_no": article_no},
            params={"mode": "view", "articleNo": article_no},
            model=SkkuArticlePostDetail,
            parse=lambda html, url: _parse_detail(
                html, url, key, SkkuArticlePostDetail
            ),
        )


class IntegratedCmsBoard(_CmsBoard[SkkuIntegratedArticlePostListItem]):
    def __init__(self, source: str, url: str) -> None:
        super().__init__(
            source,
            url,
            SkkuIntegratedArticlePostListItem,
            list[SkkuIntegratedArticlePostListItem],
            _integrated_key,
        )

    async def get_post(
        self, board_id: int, item_id: str
    ) -> SkkuIntegratedArticlePostDetail:
        key = SkkuIntegratedArticleKey(
            type="skku_article", board_id=board_id, item_id=item_id
        )
        return await self._get_detail(
            key={"board_id": board_id, "item_id": item_id},
            params={"mode": "view", "viewBoardId": board_id, "itemId": item_id},
            model=SkkuIntegratedArticlePostDetail,
            parse=lambda html, url: _parse_detail(
                html, url, key, SkkuIntegratedArticlePostDetail
            ),
        )
