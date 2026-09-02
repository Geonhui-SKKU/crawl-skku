from typing import Annotated

from fastapi import Depends

from crawl_skku.article.sco.service import ScoArticlePostService


async def get_sco_article_post_service() -> ScoArticlePostService:
    return ScoArticlePostService()


ScoArticlePostServiceDep = Annotated[
    ScoArticlePostService,
    Depends(get_sco_article_post_service),
]
