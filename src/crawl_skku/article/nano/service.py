from bs4 import BeautifulSoup

from crawl_skku import service
from crawl_skku.article import utils
from crawl_skku.article.board_markup import (
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

BOARD_URL = "https://nano.skku.edu/bbs/board.php"
BOARD_NAME = "bbs42"
PAGE_SIZE = 10


def parse_post_list(html: str) -> list[SkkuArticlePostListItem]:
    board = require_tag(BeautifulSoup(html, "html.parser"), "#sub_contents .conbody")
    posts = []
    for row in board.select("tr:has(> td.responsive03 a[href*='mode=VIEW'])"):
        link = require_tag(row, "td.responsive03 a[href*='mode=VIEW']")
        href = post_href(link)
        mobile_meta = utils.tag_text(row.select_one(".mobile_regist_date"))
        author = mobile_meta.split("|", 1)[0].strip() if "|" in mobile_meta else None
        posts.append(
            SkkuArticlePostListItem(
                key=query_key(href, "num"),
                title=require_text(link),
                date=post_date(utils.tag_text(row.select_one(".tablet_regist_date"))),
                author=author,
                url=utils.absolute_url(BOARD_URL, href),
                has_attachment=row.select_one(
                    "img[src*='file'], a[href*='download.php']"
                )
                is not None,
            )
        )
    return posts


def parse_post_detail(html: str, url: str, article_no: int) -> SkkuArticlePostDetail:
    board = require_tag(
        BeautifulSoup(html, "html.parser"), ".conbody table:has(.viewBtnArea)"
    )
    fields: dict[str, str] = {}
    for field in board.select(".bbs_top li"):
        fields[utils.tag_text(field.select_one("em"))] = utils.tag_text(
            field.select_one("span")
        )
    description, attachments = utils.parse_body(
        require_tag(board, "#DivContents"),
        board.select("a[href*='download.php']"),
        url,
    )
    return SkkuArticlePostDetail(
        key=SkkuArticleKey(type="skku_article", article_no=article_no),
        title=require_text(board.select_one("tr[height='35'] td strong")),
        date=post_date(fields.get("작성일", "")),
        author=fields.get("글쓴이") or None,
        url=url,
        description=description,
        has_attachment=bool(attachments),
        attachments=attachments or None,
    )


class NanoArticlePostService(PagedArticleBoard):
    def __init__(self) -> None:
        super().__init__("nano", BOARD_URL, PAGE_SIZE)

    async def _load_page(
        self, page: int
    ) -> tuple[list[SkkuArticlePostListItem], list[SkkuArticlePostListItem]]:
        html = await service.fetch_html(
            self.url, params={"tbl": BOARD_NAME, "page": page}
        )
        return [], parse_post_list(html)

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail:
        return await self._get_detail(
            key={"article_no": article_no},
            params={"tbl": BOARD_NAME, "mode": "VIEW", "num": article_no},
            model=SkkuArticlePostDetail,
            parse=lambda html, url: parse_post_detail(html, url, article_no),
        )
