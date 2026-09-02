import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from pydantic import BaseModel, ValidationError

from crawl_skku import cache
from crawl_skku.cache import SkkuCacheSettings, sqlite_store


class CachedItem(BaseModel):
    value: int


class SkkuCacheSettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        cache.get_cache_settings.cache_clear()
        self.addCleanup(cache.get_cache_settings.cache_clear)

    def test_cache_settings_parse_environment_variables(self) -> None:
        env = {
            "SKKU_CACHE_ENABLED": "false",
            "SKKU_CACHE_DIR": "/tmp/skku-cache",
            "SKKU_CACHE_DB_NAME": "custom.sqlite3",
            "SKKU_CACHE_LIST_TTL_SECONDS": "45",
            "SKKU_CACHE_DETAIL_TTL_SECONDS": "90",
        }

        with patch.dict(os.environ, env, clear=True):
            settings = cache.get_cache_settings()

        self.assertFalse(settings.enabled)
        self.assertEqual(settings.cache_dir, Path("/tmp/skku-cache"))
        self.assertEqual(settings.db_name, "custom.sqlite3")
        self.assertEqual(settings.list_ttl_seconds, 45)
        self.assertEqual(settings.detail_ttl_seconds, 90)
        self.assertEqual(settings.db_path, Path("/tmp/skku-cache/custom.sqlite3"))

    def test_cache_settings_parse_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            env_file = Path(tempdir) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "SKKU_CACHE_ENABLED=true",
                        "SKKU_CACHE_DIR=/tmp/env-file-cache",
                        "SKKU_CACHE_DB_NAME=env-file.sqlite3",
                        "SKKU_CACHE_LIST_TTL_SECONDS=120",
                        "SKKU_CACHE_DETAIL_TTL_SECONDS=240",
                    ]
                ),
                encoding="utf-8",
            )

            cwd = Path.cwd()
            try:
                os.chdir(tempdir)
                with patch.dict(os.environ, {}, clear=True):
                    settings = cache.get_cache_settings()
            finally:
                os.chdir(cwd)

        self.assertTrue(settings.enabled)
        self.assertEqual(settings.cache_dir, Path("/tmp/env-file-cache"))
        self.assertEqual(settings.db_name, "env-file.sqlite3")
        self.assertEqual(settings.list_ttl_seconds, 120)
        self.assertEqual(settings.detail_ttl_seconds, 240)

    def test_cache_settings_environment_overrides_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            env_file = Path(tempdir) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "SKKU_CACHE_ENABLED=false",
                        "SKKU_CACHE_LIST_TTL_SECONDS=120",
                    ]
                ),
                encoding="utf-8",
            )

            cwd = Path.cwd()
            try:
                os.chdir(tempdir)
                with patch.dict(
                    os.environ,
                    {
                        "SKKU_CACHE_ENABLED": "true",
                        "SKKU_CACHE_LIST_TTL_SECONDS": "30",
                    },
                    clear=True,
                ):
                    settings = cache.get_cache_settings()
            finally:
                os.chdir(cwd)

        self.assertTrue(settings.enabled)
        self.assertEqual(settings.list_ttl_seconds, 30)

    def test_invalid_integer_environment_value_fails_fast(self) -> None:
        with patch.dict(
            os.environ, {"SKKU_CACHE_LIST_TTL_SECONDS": "invalid"}, clear=True
        ):
            with self.assertRaises(ValidationError):
                cache.get_cache_settings()

    def test_cache_settings_accept_constructor_field_names(self) -> None:
        settings = SkkuCacheSettings(
            enabled=False,
            cache_dir=Path("/tmp/constructor-cache"),
            db_name="constructor.sqlite3",
            list_ttl_seconds=15,
            detail_ttl_seconds=30,
        )

        self.assertFalse(settings.enabled)
        self.assertEqual(settings.cache_dir, Path("/tmp/constructor-cache"))
        self.assertEqual(settings.db_name, "constructor.sqlite3")
        self.assertEqual(settings.list_ttl_seconds, 15)
        self.assertEqual(settings.detail_ttl_seconds, 30)

    def test_payload_version_is_not_environment_configurable(self) -> None:
        env = {
            "PAYLOAD_VERSION": "2",
            "SKKU_CACHE_PAYLOAD_VERSION": "3",
        }

        with patch.dict(os.environ, env, clear=True):
            settings = cache.get_cache_settings()

        self.assertEqual(settings.payload_version, 1)


class SkkuCacheTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        async def run_sync_inline(func, *args, **kwargs):
            return func(*args, **kwargs)

        self.run_in_threadpool_patcher = patch(
            "crawl_skku.cache.service.run_in_threadpool",
            new=run_sync_inline,
        )
        self.run_in_threadpool_patcher.start()
        self.addCleanup(self.run_in_threadpool_patcher.stop)

    def make_settings(self, *, enabled: bool = True) -> SkkuCacheSettings:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        return SkkuCacheSettings(
            enabled=enabled,
            cache_dir=Path(self.tempdir.name),
            db_name="test.sqlite3",
            list_ttl_seconds=300,
            detail_ttl_seconds=3600,
        )

    async def test_cache_miss_calls_loader_and_stores_payload(self) -> None:
        settings = self.make_settings()
        calls = 0

        async def loader() -> CachedItem:
            nonlocal calls
            calls += 1
            return CachedItem(value=10)

        first = await cache.get_or_load(
            namespace="test",
            resource=cache.CacheResource.POST_DETAIL,
            key={"article_no": 1},
            ttl_seconds=300,
            response_type=CachedItem,
            loader=loader,
            settings=settings,
        )
        second = await cache.get_or_load(
            namespace="test",
            resource=cache.CacheResource.POST_DETAIL,
            key={"article_no": 1},
            ttl_seconds=300,
            response_type=CachedItem,
            loader=loader,
            settings=settings,
        )

        self.assertEqual(first, CachedItem(value=10))
        self.assertEqual(second, CachedItem(value=10))
        self.assertEqual(calls, 1)

    async def test_disabled_cache_always_calls_loader(self) -> None:
        settings = self.make_settings(enabled=False)
        calls = 0

        async def loader() -> CachedItem:
            nonlocal calls
            calls += 1
            return CachedItem(value=calls)

        first = await cache.get_or_load(
            namespace="test",
            resource=cache.CacheResource.POST_DETAIL,
            key={"article_no": 1},
            ttl_seconds=300,
            response_type=CachedItem,
            loader=loader,
            settings=settings,
        )
        second = await cache.get_or_load(
            namespace="test",
            resource=cache.CacheResource.POST_DETAIL,
            key={"article_no": 1},
            ttl_seconds=300,
            response_type=CachedItem,
            loader=loader,
            settings=settings,
        )

        self.assertEqual(first.value, 1)
        self.assertEqual(second.value, 2)
        self.assertEqual(calls, 2)

    async def test_expired_payload_is_treated_as_miss(self) -> None:
        settings = self.make_settings()
        cache_key = cache.make_cache_key({"article_no": 1})
        sqlite_store.write_cache(
            settings=settings,
            namespace="test",
            resource=cache.CacheResource.POST_DETAIL,
            cache_key=cache_key,
            payload=json.dumps({"value": 1}),
        )
        expired_at = datetime.now(UTC) - timedelta(seconds=600)
        with closing(sqlite3.connect(settings.db_path)) as connection:
            with connection:
                connection.execute(
                    "UPDATE cache_entry SET cached_at = ?",
                    (expired_at.isoformat(),),
                )

        async def loader() -> CachedItem:
            return CachedItem(value=2)

        result = await cache.get_or_load(
            namespace="test",
            resource=cache.CacheResource.POST_DETAIL,
            key={"article_no": 1},
            ttl_seconds=300,
            response_type=CachedItem,
            loader=loader,
            settings=settings,
        )

        self.assertEqual(result, CachedItem(value=2))

    async def test_invalid_payload_is_treated_as_miss(self) -> None:
        settings = self.make_settings()
        cache_key = cache.make_cache_key({"article_no": 1})
        sqlite_store.write_cache(
            settings=settings,
            namespace="test",
            resource=cache.CacheResource.POST_DETAIL,
            cache_key=cache_key,
            payload="not-json",
        )

        async def loader() -> CachedItem:
            return CachedItem(value=2)

        with self.assertLogs("crawl_skku.cache", level="WARNING"):
            result = await cache.get_or_load(
                namespace="test",
                resource=cache.CacheResource.POST_DETAIL,
                key={"article_no": 1},
                ttl_seconds=300,
                response_type=CachedItem,
                loader=loader,
                settings=settings,
            )

        self.assertEqual(result, CachedItem(value=2))

    def test_cache_key_is_deterministic(self) -> None:
        self.assertEqual(
            cache.make_cache_key({"offset": 10, "limit": 5}),
            cache.make_cache_key({"limit": 5, "offset": 10}),
        )


if __name__ == "__main__":
    unittest.main()
