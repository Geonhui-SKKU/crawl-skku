"""High-level asynchronous client for supported SKKU public sources."""

from datetime import date

from crawl_skku.article import aiuniv
from crawl_skku.article.board_service import NumberedArticleBoard
from crawl_skku.article.college_sources import (
    INTEGRATED_COLLEGE_BOARDS,
    NUMBERED_COLLEGE_BOARDS,
)
from crawl_skku.article.cscience.schemas import (
    CscienceArticlePostDetail,
    SkkuCscienceArticlePostListItem,
)
from crawl_skku.article.cscience.service import CscienceArticlePostService
from crawl_skku.article.cse.service import CseArticlePostService
from crawl_skku.article.department_sources import NUMBERED_DEPARTMENT_BOARDS
from crawl_skku.article.enc.service import EncArticlePostService
from crawl_skku.article.ice.service import IceArticlePostService
from crawl_skku.article.root.service import RootArticlePostService
from crawl_skku.article.schemas import (
    SkkuArticlePostDetail,
    SkkuArticlePostListItem,
    SkkuIntegratedArticlePostDetail,
    SkkuIntegratedArticlePostListItem,
)
from crawl_skku.article.sco.service import ScoArticlePostService
from crawl_skku.article.sw.service import SwArticlePostService
from crawl_skku.calendar.root.service import RootCalendarService
from crawl_skku.calendar.schemas import SkkuCalendarDay, SkkuCalendarMonth


class CrawlSkkuClient:
    """Fetch normalized SKKU public posts and academic calendar data.

    The client uses the same parsers and cache as the FastAPI application.
    """

    def __init__(self) -> None:
        self._enc_article_service = EncArticlePostService()
        self._article_services: dict[str, NumberedArticleBoard] = {
            "root": RootArticlePostService(),
            "sw": SwArticlePostService(),
            aiuniv.SOURCE: aiuniv.board,
            "cse": CseArticlePostService(),
            "sco": ScoArticlePostService(),
            "ice": IceArticlePostService(),
            **NUMBERED_COLLEGE_BOARDS,
            **NUMBERED_DEPARTMENT_BOARDS,
        }
        self._cscience_article_service = CscienceArticlePostService()
        self._calendar_service = RootCalendarService()

    async def get_posts(
        self, source: str, *, offset: int = 0, limit: int = 10
    ) -> (
        list[SkkuArticlePostListItem]
        | list[SkkuCscienceArticlePostListItem]
        | list[SkkuIntegratedArticlePostListItem]
    ):
        if source == "cscience":
            return await self._cscience_article_service.get_posts(
                offset=offset, limit=limit
            )
        if source == "enc":
            return await self._enc_article_service.get_posts(offset=offset, limit=limit)
        if source in INTEGRATED_COLLEGE_BOARDS:
            return await INTEGRATED_COLLEGE_BOARDS[source].get_posts(
                offset=offset, limit=limit
            )
        return await self._article_service(source).get_posts(offset=offset, limit=limit)

    async def get_post(self, source: str, article_no: int) -> SkkuArticlePostDetail:
        if source == "enc":
            raise ValueError(
                "ENC posts require board_id and item_id; use get_enc_post(...)"
            )
        if source == "cscience":
            raise ValueError(
                "CScience posts require board_id and item_id; use get_cscience_post(...)"
            )
        if source in INTEGRATED_COLLEGE_BOARDS:
            raise ValueError(
                f"{source} posts require board_id and item_id; use get_integrated_post(...)"
            )
        return await self._article_service(source).get_post(article_no)

    async def get_integrated_post(
        self, source: str, board_id: int, item_id: str
    ) -> SkkuIntegratedArticlePostDetail:
        """Get a newly supported integrated-board post using the key from its list."""
        if source not in INTEGRATED_COLLEGE_BOARDS:
            sources = ", ".join(INTEGRATED_COLLEGE_BOARDS)
            raise ValueError(
                f"Unsupported integrated source {source!r}. Expected one of: {sources}"
            )
        return await INTEGRATED_COLLEGE_BOARDS[source].get_post(board_id, item_id)

    async def get_cscience_post(
        self, board_id: int, item_id: str
    ) -> CscienceArticlePostDetail:
        """Get a Natural Sciences College post by its source-specific key."""
        return await self._cscience_article_service.get_post(board_id, item_id)

    async def get_enc_post(
        self, article_no: int, board_id: int, item_id: str
    ) -> SkkuArticlePostDetail:
        """Get an Engineering College post by its current upstream identifiers."""
        return await self._enc_article_service.get_item_post(
            article_no, board_id, item_id
        )

    async def get_calendar_month(self, year: int, month: int) -> SkkuCalendarMonth:
        return await self._calendar_service.get_month(year, month)

    async def get_calendar_day(self, day: date) -> SkkuCalendarDay:
        return await self._calendar_service.get_day(day)

    def _article_service(self, source: str) -> NumberedArticleBoard:
        if source == aiuniv.LEGACY_SOURCE:
            source = aiuniv.SOURCE
        try:
            return self._article_services[source]
        except KeyError as exc:
            sources = ", ".join(
                (*self._article_services, "cscience", "enc", *INTEGRATED_COLLEGE_BOARDS)
            )
            raise ValueError(
                f"Unsupported source {source!r}. Expected one of: {sources}"
            ) from exc
