from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup

from crawl_skku import service
from crawl_skku.article import utils
from crawl_skku.article.board_markup import (
    make_attachment,
    post_date,
    post_href,
    query_key,
    require_tag,
    require_text,
)
from crawl_skku.article.paged_board import PagedArticleBoard
from crawl_skku.article.schemas import (
    SkkuArticleKey,
    SkkuArticlePostDetail,
    SkkuArticlePostListItem,
)
from crawl_skku.exceptions import SkkuParseError

BOARD_URL = "https://cal.skku.edu/index.php"
BOARD_PARAMS: dict[str, int | str] = {"hCode": "BOARD", "bo_idx": 17}
PAGE_SIZE = 20


def parse_post_list(
    html: str,
) -> tuple[list[SkkuArticlePostListItem], list[SkkuArticlePostListItem]]:
    board = require_tag(BeautifulSoup(html, "html.parser"), "table.board_table tbody")
    pinned: list[SkkuArticlePostListItem] = []
    regular: list[SkkuArticlePostListItem] = []
    for row in board.select(":scope > tr:has(a[href*='page=view'])"):
        link = require_tag(row, ".alignLeft a[href*='page=view']")
        href = post_href(link)
        cells = row.find_all("td", recursive=False)
        if len(cells) < 6:
            raise SkkuParseError("Missing CAL notice metadata")
        item = SkkuArticlePostListItem(
            key=query_key(href, "idx"),
            title=require_text(link),
            date=post_date(utils.tag_text(cells[-1])),
            category=utils.tag_text(cells[1]) or None,
            url=utils.absolute_url(BOARD_URL, href),
            has_attachment=row.select_one(".file_a a[href]") is not None,
        )
        (pinned if row.select_one(".label-warning") else regular).append(item)
    return pinned, regular


def parse_post_detail(html: str, url: str, article_no: int) -> SkkuArticlePostDetail:
    board = require_tag(BeautifulSoup(html, "html.parser"), "table.board_Vtable")
    meta = board.select("thead ul li:not(.imbar)")
    if len(meta) < 2:
        raise SkkuParseError("Missing CAL notice metadata")
    content = require_tag(board, ".board_content")
    description, attachments = utils.parse_body(content, [], url)
    for link in board.select("a[href*='nfupload_down.php']"):
        href = post_href(link)
        names = parse_qs(urlsplit(href).query).get("name")
        name = (names[0] if names else utils.tag_text(link)).strip()
        if name:
            attachments.append(make_attachment(name, href, url))
    return SkkuArticlePostDetail(
        key=SkkuArticleKey(type="skku_article", article_no=article_no),
        title=require_text(board.select_one("thead th")),
        date=post_date(utils.tag_text(meta[-1])),
        author=utils.tag_text(meta[0]) or None,
        url=url,
        description=description,
        has_attachment=bool(attachments),
        attachments=attachments or None,
    )


class CalArticlePostService(PagedArticleBoard):
    def __init__(self) -> None:
        super().__init__("cal", BOARD_URL, PAGE_SIZE, repeated_pins=True)

    async def _load_page(
        self, page: int
    ) -> tuple[list[SkkuArticlePostListItem], list[SkkuArticlePostListItem]]:
        return parse_post_list(
            await service.fetch_html(
                self.url, params={**BOARD_PARAMS, "page": "list", "pg": page}
            )
        )

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail:
        return await self._get_detail(
            key={"article_no": article_no},
            params={**BOARD_PARAMS, "page": "view", "idx": article_no},
            model=SkkuArticlePostDetail,
            parse=lambda html, url: parse_post_detail(html, url, article_no),
        )
