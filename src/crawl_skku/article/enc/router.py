from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from crawl_skku.article.enc import constants
from crawl_skku.article.enc.dependencies import EncArticlePostServiceDep
from crawl_skku.article.schemas import SkkuArticlePostDetail, SkkuArticlePostListItem
from crawl_skku.exceptions import SkkuCrawlerError

router = APIRouter(tags=["SKKU ENC posts"])


@router.get("/posts", summary="List SKKU ENC posts")
async def list_posts(
    service: EncArticlePostServiceDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[
        int, Query(ge=1, le=constants.MAX_LIMIT)
    ] = constants.DEFAULT_LIMIT,
) -> list[SkkuArticlePostListItem]:
    try:
        return await service.get_posts(offset=offset, limit=limit)
    except SkkuCrawlerError as exc:
        raise _bad_gateway(exc) from exc


@router.get(
    "/posts/{article_no}/{board_id}/{item_id}",
    summary="Get an SKKU ENC post by its current upstream identifiers",
)
async def get_item_post(
    service: EncArticlePostServiceDep,
    article_no: Annotated[int, Path(ge=1)],
    board_id: Annotated[int, Path(ge=1)],
    item_id: Annotated[str, Path(min_length=1)],
) -> SkkuArticlePostDetail:
    try:
        return await service.get_item_post(article_no, board_id, item_id)
    except SkkuCrawlerError as exc:
        raise _bad_gateway(exc) from exc


def _bad_gateway(exc: SkkuCrawlerError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(exc) or "Failed to read SKKU ENC upstream page",
    )
