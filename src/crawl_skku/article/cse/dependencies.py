from typing import Annotated

from fastapi import Depends

from crawl_skku.article.cse.service import CseArticlePostService


async def get_cse_article_post_service() -> CseArticlePostService:
    return CseArticlePostService()


CseArticlePostServiceDep = Annotated[
    CseArticlePostService,
    Depends(get_cse_article_post_service),
]
