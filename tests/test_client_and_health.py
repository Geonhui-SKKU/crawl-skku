import unittest
from datetime import date
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from crawl_skku import CrawlSkkuClient
from crawl_skku.api import app
from crawl_skku.article.schemas import SkkuArticlePostListItem


class CrawlSkkuClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_posts_delegates_to_selected_source(self) -> None:
        client = CrawlSkkuClient()
        expected = [
            SkkuArticlePostListItem(
                key={"type": "skku_article", "article_no": 1},
                category=None,
                title="Synthetic post",
                date=date(2031, 1, 1),
                author=None,
                url="https://example.test/posts/1",
            )
        ]
        service = client._article_services["root"]
        service.get_posts = AsyncMock(return_value=expected)  # type: ignore[method-assign]

        result = await client.get_posts("root", offset=2, limit=3)

        self.assertEqual(result, expected)
        service.get_posts.assert_awaited_once_with(offset=2, limit=3)

    async def test_unknown_source_is_rejected(self) -> None:
        client = CrawlSkkuClient()

        with self.assertRaisesRegex(ValueError, "Unsupported source"):
            await client.get_posts("unknown")

    def test_new_college_sources_are_available(self) -> None:
        client = CrawlSkkuClient()

        self.assertIsNotNone(client._enc_article_service)
        self.assertIn("ice", client._article_services)

    async def test_enc_list_source_uses_its_service(self) -> None:
        client = CrawlSkkuClient()
        client._enc_article_service.get_posts = AsyncMock(return_value=[])  # type: ignore[method-assign]

        await client.get_posts("enc", offset=2, limit=3)

        client._enc_article_service.get_posts.assert_awaited_once_with(  # type: ignore[attr-defined]
            offset=2, limit=3
        )

    async def test_enc_numeric_only_detail_is_rejected(self) -> None:
        client = CrawlSkkuClient()

        with self.assertRaisesRegex(ValueError, "use get_enc_post"):
            await client.get_post("enc", 1717)

    async def test_enc_detail_uses_current_identifiers(self) -> None:
        client = CrawlSkkuClient()
        client._enc_article_service.get_item_post = AsyncMock()  # type: ignore[method-assign]

        await client.get_enc_post(1717, 138885, "ABC123")

        client._enc_article_service.get_item_post.assert_awaited_once_with(  # type: ignore[attr-defined]
            1717, 138885, "ABC123"
        )

    async def test_cscience_list_source_uses_its_service(self) -> None:
        client = CrawlSkkuClient()
        client._cscience_article_service.get_posts = AsyncMock(return_value=[])  # type: ignore[method-assign]

        await client.get_posts("cscience", offset=2, limit=3)

        client._cscience_article_service.get_posts.assert_awaited_once_with(
            offset=2,
            limit=3,
        )


class HealthEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_healthz_returns_ok(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
