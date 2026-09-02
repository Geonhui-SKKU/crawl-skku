from typing import Annotated

from fastapi import Depends

from crawl_skku.article.sw.service import SwArticlePostService


async def get_sw_article_post_service() -> SwArticlePostService:
    return SwArticlePostService()


SwArticlePostServiceDep = Annotated[
    SwArticlePostService,
    Depends(get_sw_article_post_service),
]
