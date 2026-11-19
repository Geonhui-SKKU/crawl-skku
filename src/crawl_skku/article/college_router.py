from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from crawl_skku.article.board_service import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    NumberedArticleBoard,
)
from crawl_skku.article.cms import IntegratedCmsBoard
from crawl_skku.article.metadata import DETAIL_SUMMARY, LIST_SUMMARY, notice_tag
from crawl_skku.article.schemas import (
    SkkuArticlePostDetail,
    SkkuArticlePostListItem,
    SkkuIntegratedArticlePostDetail,
    SkkuIntegratedArticlePostListItem,
)
from crawl_skku.exceptions import SkkuCrawlerError

Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=MAX_LIMIT)]
PositiveId = Annotated[int, Path(ge=1)]


def numbered_router(source: str, board: NumberedArticleBoard) -> APIRouter:
    router = APIRouter(tags=[notice_tag(source)])

    @router.get("/posts", summary=LIST_SUMMARY)
    async def list_posts(
        offset: Offset = 0, limit: Limit = DEFAULT_LIMIT
    ) -> list[SkkuArticlePostListItem]:
        try:
            return await board.get_posts(offset=offset, limit=limit)
        except SkkuCrawlerError as exc:
            raise _bad_gateway(exc) from exc

    @router.get("/posts/{article_no}", summary=DETAIL_SUMMARY)
    async def get_post(article_no: PositiveId) -> SkkuArticlePostDetail:
        try:
            return await board.get_post(article_no)
        except SkkuCrawlerError as exc:
            raise _bad_gateway(exc) from exc

    return router


def integrated_router(source: str, board: IntegratedCmsBoard) -> APIRouter:
    router = APIRouter(tags=[notice_tag(source)])

    @router.get("/posts", summary=LIST_SUMMARY)
    async def list_posts(
        offset: Offset = 0, limit: Limit = DEFAULT_LIMIT
    ) -> list[SkkuIntegratedArticlePostListItem]:
        try:
            return await board.get_posts(offset, limit)
        except SkkuCrawlerError as exc:
            raise _bad_gateway(exc) from exc

    @router.get("/posts/{board_id}/{item_id}", summary=DETAIL_SUMMARY)
    async def get_post(
        board_id: PositiveId, item_id: Annotated[str, Path(min_length=1)]
    ) -> SkkuIntegratedArticlePostDetail:
        try:
            return await board.get_post(board_id, item_id)
        except SkkuCrawlerError as exc:
            raise _bad_gateway(exc) from exc

    return router


def _bad_gateway(exc: SkkuCrawlerError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(exc) or "Failed to read SKKU upstream page",
    )
