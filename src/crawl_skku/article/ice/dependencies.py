from typing import Annotated

from fastapi import Depends

from crawl_skku.article.ice.service import IceArticlePostService


async def get_ice_article_post_service() -> IceArticlePostService:
    return IceArticlePostService()


IceArticlePostServiceDep = Annotated[
    IceArticlePostService,
    Depends(get_ice_article_post_service),
]
