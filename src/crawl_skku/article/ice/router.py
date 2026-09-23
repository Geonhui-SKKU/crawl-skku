from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from crawl_skku.article.ice import constants
from crawl_skku.article.ice.dependencies import IceArticlePostServiceDep
from crawl_skku.article.schemas import SkkuArticlePostDetail, SkkuArticlePostListItem
from crawl_skku.exceptions import SkkuCrawlerError

router = APIRouter(tags=["SKKU ICE posts"])


@router.get("/posts", summary="List SKKU ICE posts")
async def list_posts(
    service: IceArticlePostServiceDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[
        int, Query(ge=1, le=constants.MAX_LIMIT)
    ] = constants.DEFAULT_LIMIT,
) -> list[SkkuArticlePostListItem]:
    try:
        return await service.get_posts(offset=offset, limit=limit)
    except SkkuCrawlerError as exc:
        raise _bad_gateway(exc) from exc


@router.get("/posts/{article_no}", summary="Get an SKKU ICE post")
async def get_post(
    service: IceArticlePostServiceDep,
    article_no: Annotated[int, Path(ge=1)],
) -> SkkuArticlePostDetail:
    try:
        return await service.get_post(article_no=article_no)
    except SkkuCrawlerError as exc:
        raise _bad_gateway(exc) from exc


def _bad_gateway(exc: SkkuCrawlerError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(exc) or "Failed to read SKKU ICE upstream page",
    )
