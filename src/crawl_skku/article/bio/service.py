import re

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
from crawl_skku.article.board_service import CachedArticleBoard
from crawl_skku.article.schemas import (
    SkkuArticleKey,
    SkkuArticlePostDetail,
    SkkuArticlePostListItem,
)

BOARD_URL = "http://bio.skku.edu/bbs/board.php"
BOARD_NAME = "N4"
PAGE_SIZE = 10


def _parse_article_numbers(html: str) -> list[int]:
    board = require_tag(BeautifulSoup(html, "html.parser"), "#bo_list tbody")
    return [
        query_key(post_href(link), "wr_id").article_no
        for link in board.select("a[href*='wr_id=']")
    ]


def parse_post_detail(html: str, url: str, article_no: int) -> SkkuArticlePostDetail:
    board = require_tag(BeautifulSoup(html, "html.parser"), "#bo_v")
    value = require_text(board.select_one("#bo_v_info .if_date"))
    value = re.sub(r"(?<!\d)(\d{2}-\d{2}-\d{2})(?!\d)", r"20\1", value, count=1)
    description, attachments = utils.parse_body(
        require_tag(board, "#bo_v_con"),
        board.select("#bo_v_file a[href*='download.php']"),
        url,
    )
    return SkkuArticlePostDetail(
        key=SkkuArticleKey(type="skku_article", article_no=article_no),
        title=require_text(board.select_one("#bo_v_title")),
        date=post_date(value),
        author=utils.tag_text(board.select_one("#bo_v_info .sv_member")) or None,
        url=url,
        description=description,
        has_attachment=bool(attachments),
        attachments=attachments or None,
    )


class BioArticlePostService(CachedArticleBoard[SkkuArticlePostListItem]):
    def __init__(self) -> None:
        super().__init__("bio", BOARD_URL, list[SkkuArticlePostListItem])

    async def _load_posts(
        self, offset: int, limit: int
    ) -> list[SkkuArticlePostListItem]:
        page_index, start = divmod(offset, PAGE_SIZE)
        result: list[SkkuArticlePostListItem] = []
        while len(result) < limit:
            html = await service.fetch_html(
                self.url, params={"bo_table": BOARD_NAME, "page": page_index + 1}
            )
            ids = _parse_article_numbers(html)
            for article_no in ids[start : start + limit - len(result)]:
                # The list only gives month/day (or time); read the actual date
                # from the cached detail instead of guessing its year.
                detail = await self.get_post(article_no)
                result.append(
                    SkkuArticlePostListItem.model_validate(detail.model_dump())
                )
            if len(ids) < PAGE_SIZE:
                break
            page_index += 1
            start = 0
        return result

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail:
        return await self._get_detail(
            key={"article_no": article_no},
            params={"bo_table": BOARD_NAME, "wr_id": article_no},
            model=SkkuArticlePostDetail,
            parse=lambda html, url: parse_post_detail(html, url, article_no),
        )
