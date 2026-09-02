import logging
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

from crawl_skku.cache.config import SkkuCacheSettings

logger = logging.getLogger(__name__)


def read_cache(
    *,
    settings: SkkuCacheSettings,
    namespace: str,
    resource: str,
    cache_key: str,
    ttl_seconds: int,
) -> str | None:
    try:
        ensure_schema(settings.db_path)
        with closing(sqlite3.connect(settings.db_path)) as connection:
            with connection:
                row = connection.execute(
                    """
                    SELECT payload, cached_at
                    FROM cache_entry
                    WHERE namespace = ?
                      AND resource = ?
                      AND cache_key = ?
                      AND payload_version = ?
                    """,
                    (namespace, resource, cache_key, settings.payload_version),
                ).fetchone()
    except (OSError, sqlite3.Error):
        logger.exception("Failed to read SKKU cache")
        return None

    if row is None:
        return None

    payload, cached_at = row
    try:
        cached_at_dt = datetime.fromisoformat(cached_at)
    except ValueError:
        return None

    if datetime.now(UTC) - cached_at_dt > timedelta(seconds=ttl_seconds):
        return None

    return str(payload)


def write_cache(
    *,
    settings: SkkuCacheSettings,
    namespace: str,
    resource: str,
    cache_key: str,
    payload: str,
) -> None:
    try:
        ensure_schema(settings.db_path)
        with closing(sqlite3.connect(settings.db_path)) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO cache_entry (
                        namespace,
                        resource,
                        cache_key,
                        payload_version,
                        payload,
                        cached_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(namespace, resource, cache_key, payload_version)
                    DO UPDATE SET
                        payload = excluded.payload,
                        cached_at = excluded.cached_at
                    """,
                    (
                        namespace,
                        resource,
                        cache_key,
                        settings.payload_version,
                        payload,
                        datetime.now(UTC).isoformat(),
                    ),
                )
    except (OSError, sqlite3.Error):
        logger.exception("Failed to write SKKU cache")


def ensure_schema(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entry (
                    namespace TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    cache_key TEXT NOT NULL,
                    payload_version INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    cached_at TEXT NOT NULL,
                    PRIMARY KEY (
                        namespace,
                        resource,
                        cache_key,
                        payload_version
                    )
                )
                """,
            )
