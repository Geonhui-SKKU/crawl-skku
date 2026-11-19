from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, Protocol, TypeVar
from urllib.parse import urlencode

from pydantic import BaseModel

from crawl_skku import cache, service
from crawl_skku.article.schemas import SkkuArticlePostDetail, SkkuArticlePostListItem

DEFAULT_LIMIT = 10
MAX_LIMIT = 50

PostT = TypeVar("PostT", bound=BaseModel)
DetailT = TypeVar("DetailT", bound=BaseModel)


class NumberedArticleBoard(Protocol):
    async def get_posts(
        self, *, offset: int, limit: int
    ) -> list[SkkuArticlePostListItem]: ...

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail: ...


class CachedArticleBoard(ABC, Generic[PostT]):
    def __init__(self, source: str, url: str, list_model: type[list[PostT]]) -> None:
        self.url = url
        self._namespace = f"crawl_skku.article.{source}"
        self._list_model = list_model

    async def get_posts(
        self, offset: int = 0, limit: int = DEFAULT_LIMIT
    ) -> list[PostT]:
        if offset < 0 or not 1 <= limit <= MAX_LIMIT:
            raise ValueError(
                f"Expected offset >= 0 and limit between 1 and {MAX_LIMIT}"
            )
        settings = cache.get_cache_settings()
        return await cache.get_or_load(
            namespace=self._namespace,
            resource=cache.CacheResource.POST_LIST,
            key={"offset": offset, "limit": limit},
            ttl_seconds=cache.list_ttl(settings),
            response_type=self._list_model,
            loader=lambda: self._load_posts(offset, limit),
            settings=settings,
        )

    @abstractmethod
    async def _load_posts(self, offset: int, limit: int) -> list[PostT]: ...

    async def _get_detail(
        self,
        *,
        key: dict[str, int | str],
        params: dict[str, int | str],
        model: type[DetailT],
        parse: Callable[[str, str], DetailT],
        url: str | None = None,
    ) -> DetailT:
        async def load() -> DetailT:
            request_url = url or self.url
            html = await service.fetch_html(request_url, params=params)
            detail_url = f"{request_url}?{urlencode(params)}" if params else request_url
            return parse(html, detail_url)

        settings = cache.get_cache_settings()
        return await cache.get_or_load(
            namespace=self._namespace,
            resource=cache.CacheResource.POST_DETAIL,
            key=key,
            ttl_seconds=cache.detail_ttl(settings),
            response_type=model,
            loader=load,
            settings=settings,
        )
