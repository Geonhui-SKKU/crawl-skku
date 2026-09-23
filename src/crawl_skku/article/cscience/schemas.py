from typing import Literal

from pydantic import Field

from crawl_skku.article.schemas import ArticlePostDetail, ArticlePostKey


class CscienceArticleKey(ArticlePostKey):
    type: Literal["cscience_article"]
    board_id: int = Field(ge=1)
    item_id: str = Field(min_length=1)


class CscienceArticlePostDetail(ArticlePostDetail):
    key: CscienceArticleKey
