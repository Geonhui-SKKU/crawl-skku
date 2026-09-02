from typing import Annotated

from fastapi import Depends

from crawl_skku.article.root.service import RootArticlePostService


async def get_root_article_post_service() -> RootArticlePostService:
    return RootArticlePostService()


RootArticlePostServiceDep = Annotated[
    RootArticlePostService,
    Depends(get_root_article_post_service),
]
