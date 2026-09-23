from typing import Annotated

from fastapi import Depends

from crawl_skku.article.cscience.service import CscienceArticlePostService


async def get_cscience_article_post_service() -> CscienceArticlePostService:
    return CscienceArticlePostService()


CscienceArticlePostServiceDep = Annotated[
    CscienceArticlePostService,
    Depends(get_cscience_article_post_service),
]
