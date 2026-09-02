from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic import Field, PositiveInt

from crawl_skku.config import EnvSettings


@dataclass(frozen=True)
class SkkuCacheSettings:
    enabled: bool = True
    cache_dir: Path = Path(".cache/crawl-skku")
    db_name: str = "skku_cache.sqlite3"
    list_ttl_seconds: PositiveInt = 300
    detail_ttl_seconds: PositiveInt = 3600
    payload_version: int = 1

    @property
    def db_path(self) -> Path:
        return self.cache_dir / self.db_name


class _SkkuCacheEnvSettings(EnvSettings):
    enabled: bool = Field(
        validation_alias="SKKU_CACHE_ENABLED", default=SkkuCacheSettings.enabled
    )
    cache_dir: Path = Field(
        validation_alias="SKKU_CACHE_DIR", default=SkkuCacheSettings.cache_dir
    )
    db_name: str = Field(
        validation_alias="SKKU_CACHE_DB_NAME", default=SkkuCacheSettings.db_name
    )
    list_ttl_seconds: PositiveInt = Field(
        validation_alias="SKKU_CACHE_LIST_TTL_SECONDS",
        default=SkkuCacheSettings.list_ttl_seconds,
    )
    detail_ttl_seconds: PositiveInt = Field(
        validation_alias="SKKU_CACHE_DETAIL_TTL_SECONDS",
        default=SkkuCacheSettings.detail_ttl_seconds,
    )


@lru_cache(maxsize=1)
def get_cache_settings() -> SkkuCacheSettings:
    env_settings = _SkkuCacheEnvSettings()
    return SkkuCacheSettings(
        enabled=env_settings.enabled,
        cache_dir=env_settings.cache_dir,
        db_name=env_settings.db_name,
        list_ttl_seconds=env_settings.list_ttl_seconds,
        detail_ttl_seconds=env_settings.detail_ttl_seconds,
    )
