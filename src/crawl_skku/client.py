"""High-level asynchronous client for supported SKKU public sources."""

from datetime import date
from typing import Protocol

from crawl_skku.article.cscience.schemas import (
    CscienceArticlePostDetail,
    SkkuCscienceArticlePostListItem,
)
from crawl_skku.article.cscience.service import CscienceArticlePostService
from crawl_skku.article.cse.service import CseArticlePostService
from crawl_skku.article.enc.service import EncArticlePostService
from crawl_skku.article.ice.service import IceArticlePostService
from crawl_skku.article.root.service import RootArticlePostService
from crawl_skku.article.schemas import SkkuArticlePostDetail, SkkuArticlePostListItem
from crawl_skku.article.sco.service import ScoArticlePostService
from crawl_skku.article.skb_swuniv.service import SkbSwunivArticlePostService
from crawl_skku.article.sw.service import SwArticlePostService
from crawl_skku.calendar.root.service import RootCalendarService
from crawl_skku.calendar.schemas import SkkuCalendarDay, SkkuCalendarMonth


class _ArticlePostService(Protocol):
    async def get_posts(
        self, *, offset: int, limit: int
    ) -> list[SkkuArticlePostListItem]: ...

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail: ...


class CrawlSkkuClient:
    """Fetch normalized SKKU public posts and academic calendar data.

    The client uses the same parsers and cache as the FastAPI application.
    """

    def __init__(self) -> None:
        self._article_services: dict[str, _ArticlePostService] = {
            "root": RootArticlePostService(),
            "sw": SwArticlePostService(),
            "skb_swuniv": SkbSwunivArticlePostService(),
            "cse": CseArticlePostService(),
            "sco": ScoArticlePostService(),
            "enc": EncArticlePostService(),
            "ice": IceArticlePostService(),
        }
        self._cscience_article_service = CscienceArticlePostService()
        self._calendar_service = RootCalendarService()

    async def get_posts(
        self, source: str, *, offset: int = 0, limit: int = 10
    ) -> list[SkkuArticlePostListItem] | list[SkkuCscienceArticlePostListItem]:
        if source == "cscience":
            return await self._cscience_article_service.get_posts(
                offset=offset, limit=limit
            )
        return await self._article_service(source).get_posts(offset=offset, limit=limit)

    async def get_post(self, source: str, article_no: int) -> SkkuArticlePostDetail:
        return await self._article_service(source).get_post(article_no)

    async def get_cscience_post(
        self, board_id: int, item_id: str
    ) -> CscienceArticlePostDetail:
        """Get a Natural Sciences College post by its source-specific key."""
        return await self._cscience_article_service.get_post(board_id, item_id)

    async def get_calendar_month(self, year: int, month: int) -> SkkuCalendarMonth:
        return await self._calendar_service.get_month(year, month)

    async def get_calendar_day(self, day: date) -> SkkuCalendarDay:
        return await self._calendar_service.get_day(day)

    def _article_service(self, source: str) -> _ArticlePostService:
        try:
            return self._article_services[source]
        except KeyError as exc:
            sources = ", ".join(self._article_services)
            raise ValueError(
                f"Unsupported source {source!r}. Expected one of: {sources}"
            ) from exc
