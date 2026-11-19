import re
from datetime import date

from bs4 import BeautifulSoup, Tag

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

BOARD_URL = "https://chem.skku.edu/chem/News/notice.do"
PAGE_SIZE = 10
DOWNLOAD = re.compile(
    r"""^\s*location\.href\s*=\s*(['"])(\?mode=download&[^'"]+)\1\s*;?\s*$"""
)


def _metadata(root: Tag) -> tuple[date, str | None]:
    fields = {}
    for tag in root.select(".noticeInfoList li"):
        label, _, value = utils.tag_text(tag).partition(":")
        fields[label.strip()] = value.strip()
    return post_date(fields.get("POSTED DATE", "")), fields.get("WRITER") or None


def parse_post_list(html: str) -> list[SkkuArticlePostListItem]:
    board = require_tag(BeautifulSoup(html, "html.parser"), ".noticeList")
    posts = []
    for row in board.select(":scope > li:has(.noticeTit)"):
        if utils.tag_text(row.select_one(".noticeTit")) == "No new posts.":
            continue
        link = require_tag(row, ".noticeTit a[href]")
        href = post_href(link)
        day, author = _metadata(row)
        posts.append(
            SkkuArticlePostListItem(
                key=query_key(href, "articleNo"),
                title=require_text(link),
                date=day,
                author=author,
                url=utils.absolute_url(BOARD_URL, href),
                has_attachment=row.select_one(".fileBtn, .fileIcon") is not None,
            )
        )
    return posts


def parse_post_detail(html: str, url: str, article_no: int) -> SkkuArticlePostDetail:
    soup = BeautifulSoup(html, "html.parser")
    board = require_tag(soup, ".board.view")
    day, author = _metadata(board)
    links = board.select("a[href*='mode=download']")
    for button in board.select(".fileBtn[onclick]"):
        onclick = button.get("onclick")
        match = DOWNLOAD.fullmatch(onclick) if isinstance(onclick, str) else None
        if match and (name := utils.tag_text(button)):
            link = soup.new_tag("a", href=match[2])
            link.string = name
            links.append(link)
    description, attachments = utils.parse_body(
        require_tag(board, ".fr-view"), links, url
    )
    return SkkuArticlePostDetail(
        key=SkkuArticleKey(type="skku_article", article_no=article_no),
        title=require_text(board.select_one(".noticeTit")),
        date=day,
        author=author,
        url=url,
        description=description,
        has_attachment=bool(attachments),
        attachments=attachments or None,
    )


class ChemArticlePostService(PagedArticleBoard):
    def __init__(self) -> None:
        super().__init__("chem", BOARD_URL, PAGE_SIZE)

    async def _load_page(
        self, page: int
    ) -> tuple[list[SkkuArticlePostListItem], list[SkkuArticlePostListItem]]:
        html = await service.fetch_html(
            self.url,
            params={
                "article.offset": (page - 1) * PAGE_SIZE,
                "articleLimit": PAGE_SIZE,
            },
        )
        return [], parse_post_list(html)

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail:
        return await self._get_detail(
            key={"article_no": article_no},
            params={"mode": "view", "articleNo": article_no},
            model=SkkuArticlePostDetail,
            parse=lambda html, url: parse_post_detail(html, url, article_no),
        )
