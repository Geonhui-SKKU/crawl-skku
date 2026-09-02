import unittest
from datetime import date

from httpx import ASGITransport, AsyncClient

from crawl_skku.api import app
from crawl_skku.article.root.dependencies import get_root_article_post_service
from crawl_skku.article.schemas import SkkuArticlePostDetail, SkkuArticlePostListItem
from crawl_skku.exceptions import SkkuFetchError


class FakeRootArticleService:
    def __init__(self) -> None:
        self.list_args: tuple[int, int] | None = None
        self.detail_article_no: int | None = None

    async def get_posts(
        self,
        offset: int,
        limit: int,
    ) -> list[SkkuArticlePostListItem]:
        self.list_args = (offset, limit)
        return [
            SkkuArticlePostListItem(
                key={"type": "skku_article", "article_no": 137555},
                category="General",
                title="Synthetic post",
                date=date(2031, 2, 14),
                author="Example Admin",
                url="https://example.test/posts/137555",
            ),
        ]

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail:
        self.detail_article_no = article_no
        return SkkuArticlePostDetail(
            key={"type": "skku_article", "article_no": article_no},
            category=None,
            title="Synthetic detail post",
            date=date(2031, 2, 8),
            author="Example Team",
            url=f"https://example.test/posts/{article_no}",
            description="Synthetic body text.",
            attachments=None,
        )


class FailingRootArticleService(FakeRootArticleService):
    async def get_posts(
        self,
        offset: int,
        limit: int,
    ) -> list[SkkuArticlePostListItem]:
        raise SkkuFetchError("upstream unavailable")


class SkkuRootArticleRouterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        app.dependency_overrides.clear()

    async def test_list_posts_uses_service_dependency(self) -> None:
        fake = FakeRootArticleService()

        async def override_service() -> FakeRootArticleService:
            return fake

        app.dependency_overrides[get_root_article_post_service] = override_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/skku/article/root/posts?offset=10&limit=5")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(fake.list_args, (10, 5))
        payload = response.json()
        self.assertNotIn("article_no", payload[0])
        self.assertEqual(payload[0]["key"]["type"], "skku_article")
        self.assertEqual(payload[0]["key"]["article_no"], 137555)
        self.assertEqual(payload[0]["date"], "2031-02-14")

    async def test_get_post_uses_service_dependency(self) -> None:
        fake = FakeRootArticleService()

        async def override_service() -> FakeRootArticleService:
            return fake

        app.dependency_overrides[get_root_article_post_service] = override_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/skku/article/root/posts/137564")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(fake.detail_article_no, 137564)
        payload = response.json()
        self.assertNotIn("article_no", payload)
        self.assertEqual(payload["key"]["type"], "skku_article")
        self.assertEqual(payload["key"]["article_no"], 137564)
        self.assertEqual(payload["description"], "Synthetic body text.")

    async def test_upstream_errors_return_bad_gateway(self) -> None:
        async def override_service() -> FailingRootArticleService:
            return FailingRootArticleService()

        app.dependency_overrides[get_root_article_post_service] = override_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/skku/article/root/posts")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "upstream unavailable")


if __name__ == "__main__":
    unittest.main()
