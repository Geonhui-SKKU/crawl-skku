from typing import Literal

from pydantic import Field

from crawl_skku.article.schemas import (
    ArticleAttachment,
    ArticlePostBase,
    ArticlePostKey,
)


class CscienceArticleKey(ArticlePostKey):
    type: Literal["cscience_article"]
    board_id: int = Field(ge=1)
    item_id: str = Field(min_length=1)


class SkkuCscienceArticlePostListItem(ArticlePostBase):
    key: CscienceArticleKey


class CscienceArticlePostDetail(SkkuCscienceArticlePostListItem):
    description: str
    attachments: list[ArticleAttachment] | None = None
    key: CscienceArticleKey
