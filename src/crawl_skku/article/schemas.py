from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ArticleAttachment(BaseModel):
    file_format: str = Field(min_length=1)
    name: str = Field(min_length=1)
    url: str = Field(min_length=1)


class ArticlePostKey(BaseModel):
    model_config = ConfigDict(extra="allow")


class SkkuArticleKey(ArticlePostKey):
    type: Literal["skku_article"]
    article_no: int = Field(ge=1)


class ArticlePostBase(BaseModel):
    category: str | None = None
    title: str = Field(min_length=1)
    date: date
    author: str | None = None
    url: str = Field(min_length=1)
    has_attachment: bool = False


class ArticlePostListItem(ArticlePostBase):
    key: ArticlePostKey


class ArticlePostDetail(ArticlePostListItem):
    description: str
    attachments: list[ArticleAttachment] | None = None


class SkkuArticlePostListItem(ArticlePostBase):
    key: SkkuArticleKey


class SkkuArticlePostDetail(SkkuArticlePostListItem):
    description: str
    attachments: list[ArticleAttachment] | None = None
