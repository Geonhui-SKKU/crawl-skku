import re
from datetime import date
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup, Tag

from crawl_skku import service
from crawl_skku.article import utils
from crawl_skku.article.paged_board import PagedArticleBoard
from crawl_skku.article.schemas import (
    SkkuArticleKey,
    SkkuArticlePostDetail,
    SkkuArticlePostListItem,
)
from crawl_skku.exceptions import SkkuParseError

BOARD_URL = "https://pharm.skku.edu/bbs/board.php"
BOARD_NAME = "notice"
PAGE_SIZE = 10


def _post_date(tag: Tag | None) -> date:
    value = utils.tag_text(tag)
    # The list uses YYYY-MM-DD; detail displays "등록일 YY-MM-DD".
    value = re.sub(r"(?<!\d)(\d{2}-\d{2}-\d{2})(?!\d)", r"20\1", value, count=1)
    try:
        return utils.parse_date(value)
    except ValueError as exc:
        raise SkkuParseError("Could not parse SKKU Pharmacy post date") from exc


def parse_post_list(html: str, url: str = BOARD_URL) -> list[SkkuArticlePostListItem]:
    board = BeautifulSoup(html, "html.parser").select_one("#board_list")
    if board is None:
        raise SkkuParseError("Could not find SKKU Pharmacy post list")
    posts = []
    for row in board.select(":scope > li"):
        if "no_data" in row.get_attribute_list("class"):
            continue
        link = row.select_one("a[href*='wr_id=']")
        title_tag = row.select_one(".bo_info h2")
        href = link.get("href") if link else None
        if not isinstance(href, str) or title_tag is None:
            raise SkkuParseError("Could not find SKKU Pharmacy post link or title")
        try:
            query = parse_qs(urlsplit(href).query)
            key = SkkuArticleKey(type="skku_article", article_no=int(query["wr_id"][0]))
        except (KeyError, ValueError) as exc:
            raise SkkuParseError("Invalid SKKU Pharmacy post identifier") from exc
        for badge in title_tag.select(".category"):
            badge.decompose()
        title = utils.tag_text(title_tag)
        if not title:
            raise SkkuParseError("Could not parse SKKU Pharmacy post title")
        posts.append(
            SkkuArticlePostListItem(
                key=key,
                title=title,
                author=utils.tag_text(row.select_one(".bo_info .write")) or None,
                date=_post_date(row.select_one(".bo_info .time")),
                url=utils.absolute_url(url, href),
                has_attachment=row.select_one(".lst_file") is not None,
            )
        )
    return posts


def parse_post_detail(html: str, url: str, article_no: int) -> SkkuArticlePostDetail:
    box = BeautifulSoup(html, "html.parser").select_one("#bo_view")
    if box is None:
        raise SkkuParseError("Could not find SKKU Pharmacy post detail")
    title = utils.tag_text(box.select_one("header h1"))
    content = box.select_one(".new_contents")
    if not title or content is None:
        raise SkkuParseError("Could not find SKKU Pharmacy post title or body")
    description, attachments = utils.parse_body(
        content, box.select(".bo_file a[href*='download.php']"), url
    )
    return SkkuArticlePostDetail(
        key=SkkuArticleKey(type="skku_article", article_no=article_no),
        title=title,
        category=utils.tag_text(box.select_one("header .cate")) or None,
        author=utils.tag_text(box.select_one("header .write")) or None,
        date=_post_date(box.select_one("header .time")),
        url=url,
        description=description,
        has_attachment=bool(attachments),
        attachments=attachments or None,
    )


class PharmArticlePostService(PagedArticleBoard):
    def __init__(
        self,
        source: str = "pharm",
        url: str = BOARD_URL,
        page_size: int = PAGE_SIZE,
    ) -> None:
        super().__init__(source, url, page_size)

    async def _load_page(
        self, page: int
    ) -> tuple[list[SkkuArticlePostListItem], list[SkkuArticlePostListItem]]:
        html = await service.fetch_html(
            self.url, params={"bo_table": BOARD_NAME, "page": page}
        )
        return [], parse_post_list(html, self.url)

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail:
        return await self._get_detail(
            key={"article_no": article_no},
            params={"bo_table": BOARD_NAME, "wr_id": article_no},
            model=SkkuArticlePostDetail,
            parse=lambda html, url: parse_post_detail(html, url, article_no),
        )
