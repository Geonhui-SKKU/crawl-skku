import json
import logging
from collections.abc import Awaitable, Callable, Mapping
from enum import StrEnum
from typing import Any, TypeVar

from fastapi.concurrency import run_in_threadpool
from pydantic import TypeAdapter, ValidationError

from crawl_skku.cache.config import SkkuCacheSettings, get_cache_settings
from crawl_skku.cache.keys import make_cache_key
from crawl_skku.cache.sqlite_store import read_cache, write_cache

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheResource(StrEnum):
    POST_LIST = "post_list"
    POST_DETAIL = "post_detail"
    CALENDAR_MONTH = "calendar_month"
    CALENDAR_DAY = "calendar_day"


async def get_or_load(
    *,
    namespace: str,
    resource: CacheResource,
    key: Mapping[str, Any],
    ttl_seconds: int,
    response_type: type[T],
    loader: Callable[[], Awaitable[T]],
    settings: SkkuCacheSettings | None = None,
) -> T:
    cache_settings = settings or get_cache_settings()
    adapter = TypeAdapter(response_type)

    if not cache_settings.enabled:
        return await loader()

    cache_key = make_cache_key(key)
    cached = await run_in_threadpool(
        read_cache,
        settings=cache_settings,
        namespace=namespace,
        resource=resource,
        cache_key=cache_key,
        ttl_seconds=ttl_seconds,
    )
    if cached is not None:
        try:
            return adapter.validate_python(json.loads(cached))
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
            logger.warning(
                "Ignoring invalid SKKU cache payload",
                extra={
                    "namespace": namespace,
                    "resource": resource,
                    "cache_key": cache_key,
                },
            )

    result = await loader()
    payload = json.dumps(
        adapter.dump_python(result, mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    await run_in_threadpool(
        write_cache,
        settings=cache_settings,
        namespace=namespace,
        resource=resource,
        cache_key=cache_key,
        payload=payload,
    )
    return result


def list_ttl(settings: SkkuCacheSettings | None = None) -> int:
    return (settings or get_cache_settings()).list_ttl_seconds


def detail_ttl(settings: SkkuCacheSettings | None = None) -> int:
    return (settings or get_cache_settings()).detail_ttl_seconds
