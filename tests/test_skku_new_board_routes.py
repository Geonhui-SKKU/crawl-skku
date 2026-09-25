import unittest
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from crawl_skku.api import app
from crawl_skku.article.enc.dependencies import get_enc_article_post_service
from crawl_skku.article.enc.utils import parse_post_detail
from tests.test_skku_article_enc_ice_utils import ENC_CURRENT_DETAIL_HTML


class SkkuNewBoardRouteTests(unittest.TestCase):
    def test_openapi_contains_new_board_routes(self) -> None:
        paths = app.openapi()["paths"]

        self.assertIn("/skku/article/sw/posts", paths)
        self.assertIn("/skku/article/sw/posts/{article_no}", paths)
        self.assertIn("/skku/article/skb_swuniv/posts", paths)
        self.assertIn("/skku/article/skb_swuniv/posts/{article_no}", paths)
        self.assertIn("/skku/article/cse/posts", paths)
        self.assertIn("/skku/article/cse/posts/{article_no}", paths)
        self.assertIn("/skku/article/cscience/posts", paths)
        self.assertIn("/skku/article/cscience/posts/{board_id}/{item_id}", paths)
        self.assertIn("/skku/article/sco/posts", paths)
        self.assertIn("/skku/article/sco/posts/{article_no}", paths)
        self.assertIn("/skku/article/enc/posts", paths)
        self.assertNotIn("/skku/article/enc/posts/{article_no}", paths)
        self.assertIn(
            "/skku/article/enc/posts/{article_no}/{board_id}/{item_id}", paths
        )
        self.assertIn("/skku/article/ice/posts", paths)
        self.assertIn("/skku/article/ice/posts/{article_no}", paths)

    def test_openapi_article_routes_have_single_source_tag(self) -> None:
        paths = app.openapi()["paths"]

        self.assertEqual(
            paths["/skku/article/sw/posts"]["get"]["tags"],
            ["SKKU SW posts"],
        )
        self.assertEqual(
            paths["/skku/article/skb_swuniv/posts"]["get"]["tags"],
            ["SKKU SKB SWUNIV posts"],
        )
        self.assertEqual(
            paths["/skku/article/cse/posts"]["get"]["tags"],
            ["SKKU CSE posts"],
        )
        self.assertEqual(
            paths["/skku/article/cscience/posts"]["get"]["tags"],
            ["SKKU CScience posts"],
        )
        self.assertEqual(
            paths["/skku/article/sco/posts"]["get"]["tags"],
            ["SKKU SCO posts"],
        )
        self.assertEqual(
            paths["/skku/article/enc/posts"]["get"]["tags"],
            ["SKKU ENC posts"],
        )
        self.assertEqual(
            paths["/skku/article/ice/posts"]["get"]["tags"],
            ["SKKU ICE posts"],
        )


class SkkuEncItemRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        app.dependency_overrides.clear()

    async def test_current_enc_detail_route_preserves_identifiers(self) -> None:
        service = AsyncMock()
        service.get_item_post.return_value = parse_post_detail(
            ENC_CURRENT_DETAIL_HTML, 1717, 138885, "ABC123"
        )

        async def override_service():
            return service

        app.dependency_overrides[get_enc_article_post_service] = override_service
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/skku/article/enc/posts/1717/138885/ABC123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["key"],
            {
                "type": "skku_article",
                "article_no": 1717,
                "board_id": 138885,
                "item_id": "ABC123",
            },
        )
        service.get_item_post.assert_awaited_once_with(1717, 138885, "ABC123")

    async def test_obsolete_enc_detail_route_is_absent(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/skku/article/enc/posts/1717")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
