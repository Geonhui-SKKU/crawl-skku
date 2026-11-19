from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from crawl_skku import service
from crawl_skku.article import utils
from crawl_skku.article.board_markup import (
    make_attachment,
    post_date,
    post_href,
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

BOARD_URL = "https://does.skku.edu/board/notice"
PAGE_SIZE = 12


def parse_post_list(html: str) -> list[SkkuArticlePostListItem]:
    board = require_tag(
        BeautifulSoup(html, "html.parser"),
        "main section:has(form[action='/board/notice'])",
    )
    posts = []
    for link in board.select("li > a[href^='/board/notice/']"):
        href = post_href(link)
        try:
            key = SkkuArticleKey(
                type="skku_article",
                article_no=int(urlsplit(href).path.rsplit("/", 1)[-1]),
            )
        except ValueError as exc:
            raise SkkuParseError("Invalid Energy Science notice identifier") from exc
        posts.append(
            SkkuArticlePostListItem(
                key=key,
                title=require_text(link.select_one(".leading-snug")),
                date=post_date(utils.tag_text(link.select_one("time"))),
                url=utils.absolute_url(BOARD_URL, href),
                has_attachment=link.select_one("span.inline-flex svg") is not None,
            )
        )
    return posts


def parse_post_detail(html: str, url: str, article_no: int) -> SkkuArticlePostDetail:
    board = require_tag(BeautifulSoup(html, "html.parser"), "main article")
    description, attachments = utils.parse_body(
        require_tag(board, ".board-body"), [], url
    )
    for link in board.select("a[href^='/files/']"):
        name = utils.tag_text(link.select_one("span")) or utils.tag_text(link)
        if name:
            attachments.append(make_attachment(name, post_href(link), url))
    return SkkuArticlePostDetail(
        key=SkkuArticleKey(type="skku_article", article_no=article_no),
        title=require_text(board.select_one("header h1")),
        date=post_date(
            utils.tag_text(board.select_one("header time, header .font-mono"))
        ),
        url=url,
        description=description,
        has_attachment=bool(attachments),
        attachments=attachments or None,
    )


class DoesArticlePostService(PagedArticleBoard):
    def __init__(self) -> None:
        super().__init__("does", BOARD_URL, PAGE_SIZE)

    async def _load_page(
        self, page: int
    ) -> tuple[list[SkkuArticlePostListItem], list[SkkuArticlePostListItem]]:
        return [], parse_post_list(
            await service.fetch_html(self.url, params={"page": page})
        )

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail:
        return await self._get_detail(
            key={"article_no": article_no},
            params={},
            url=f"{self.url}/{article_no}",
            model=SkkuArticlePostDetail,
            parse=lambda html, url: parse_post_detail(html, url, article_no),
        )
