from typing import Annotated

from fastapi import Depends

from crawl_skku.article.skb_swuniv.service import SkbSwunivArticlePostService


async def get_skb_swuniv_article_post_service() -> SkbSwunivArticlePostService:
    return SkbSwunivArticlePostService()


SkbSwunivArticlePostServiceDep = Annotated[
    SkbSwunivArticlePostService,
    Depends(get_skb_swuniv_article_post_service),
]
