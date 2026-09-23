from typing import Annotated

from fastapi import Depends

from crawl_skku.article.enc.service import EncArticlePostService


async def get_enc_article_post_service() -> EncArticlePostService:
    return EncArticlePostService()


EncArticlePostServiceDep = Annotated[
    EncArticlePostService,
    Depends(get_enc_article_post_service),
]
