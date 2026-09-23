from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from crawl_skku.article.cscience import constants
from crawl_skku.article.cscience.dependencies import CscienceArticlePostServiceDep
from crawl_skku.article.cscience.schemas import (
    CscienceArticlePostDetail,
    SkkuCscienceArticlePostListItem,
)
from crawl_skku.exceptions import SkkuCrawlerError

router = APIRouter(tags=["SKKU CScience posts"])


@router.get("/posts", summary="List SKKU CScience posts")
async def list_posts(
    service: CscienceArticlePostServiceDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[
        int, Query(ge=1, le=constants.MAX_LIMIT)
    ] = constants.DEFAULT_LIMIT,
) -> list[SkkuCscienceArticlePostListItem]:
    try:
        return await service.get_posts(offset=offset, limit=limit)
    except SkkuCrawlerError as exc:
        raise _bad_gateway(exc) from exc


@router.get(
    "/posts/{board_id}/{item_id}",
    summary="Get an SKKU CScience post",
)
async def get_post(
    service: CscienceArticlePostServiceDep,
    board_id: Annotated[int, Path(ge=1)],
    item_id: Annotated[str, Path(min_length=1)],
) -> CscienceArticlePostDetail:
    try:
        return await service.get_post(board_id=board_id, item_id=item_id)
    except SkkuCrawlerError as exc:
        raise _bad_gateway(exc) from exc


def _bad_gateway(exc: SkkuCrawlerError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(exc) or "Failed to read SKKU CScience upstream page",
    )
