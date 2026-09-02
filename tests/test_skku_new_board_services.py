import unittest
from unittest.mock import AsyncMock, patch

from crawl_skku import cache as skku_cache
from crawl_skku.article.cse import constants as cse_constants
from crawl_skku.article.cse.service import CseArticlePostService
from crawl_skku.article.sco import constants as sco_constants
from crawl_skku.article.sco.service import ScoArticlePostService
from crawl_skku.article.skb_swuniv import constants as skb_constants
from crawl_skku.article.skb_swuniv.service import SkbSwunivArticlePostService
from crawl_skku.article.sw import constants as sw_constants
from crawl_skku.article.sw.service import SwArticlePostService
from tests.test_skku_article_cse_utils import DETAIL_HTML as CSE_DETAIL_HTML
from tests.test_skku_article_cse_utils import LIST_HTML as CSE_LIST_HTML
from tests.test_skku_article_sco_utils import DETAIL_HTML as SCO_DETAIL_HTML
from tests.test_skku_article_sco_utils import LIST_HTML as SCO_LIST_HTML
from tests.test_skku_article_skb_swuniv_utils import DETAIL_HTML as SKB_DETAIL_HTML
from tests.test_skku_article_skb_swuniv_utils import LIST_HTML as SKB_LIST_HTML
from tests.test_skku_article_sw_utils import DETAIL_HTML as SW_DETAIL_HTML
from tests.test_skku_article_sw_utils import LIST_HTML as SW_LIST_HTML


class SkkuNewBoardServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_sw_list_uses_cache_namespace_and_offset_key(self) -> None:
        fetch_html = AsyncMock(return_value=SW_LIST_HTML)

        with (
            patch("crawl_skku.article.sw.service.skku_service.fetch_html", fetch_html),
            patch(
                "crawl_skku.article.sw.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            items = await SwArticlePostService().get_posts(offset=10, limit=5)

        fetch_html.assert_awaited_once_with(
            sw_constants.BOARD_BASE_URL,
            params={"article.offset": 10, "articleLimit": 5},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["namespace"], sw_constants.BOARD_NAME
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"], skku_cache.CacheResource.POST_LIST
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["key"], {"offset": 10, "limit": 5}
        )
        self.assertEqual(items[0].key.type, "skku_article")
        self.assertEqual(items[0].key.article_no, 218961)

    async def test_sw_detail_uses_cache_namespace_and_article_key(self) -> None:
        fetch_html = AsyncMock(return_value=SW_DETAIL_HTML)

        with (
            patch("crawl_skku.article.sw.service.skku_service.fetch_html", fetch_html),
            patch(
                "crawl_skku.article.sw.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            detail = await SwArticlePostService().get_post(article_no=218961)

        fetch_html.assert_awaited_once_with(
            sw_constants.BOARD_BASE_URL,
            params={"mode": "view", "articleNo": 218961},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["namespace"], sw_constants.BOARD_NAME
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"],
            skku_cache.CacheResource.POST_DETAIL,
        )
        self.assertEqual(get_or_load.call_args.kwargs["key"], {"article_no": 218961})
        self.assertEqual(detail.key.type, "skku_article")
        self.assertEqual(detail.key.article_no, 218961)

    async def test_skb_list_uses_cache_namespace_and_offset_key(self) -> None:
        fetch_html = AsyncMock(return_value=SKB_LIST_HTML)

        with (
            patch(
                "crawl_skku.article.skb_swuniv.service.skku_service.fetch_html",
                fetch_html,
            ),
            patch(
                "crawl_skku.article.skb_swuniv.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            items = await SkbSwunivArticlePostService().get_posts(offset=10, limit=5)

        fetch_html.assert_awaited_once_with(
            skb_constants.BOARD_BASE_URL,
            params={"article.offset": 10, "articleLimit": 5},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["namespace"], skb_constants.BOARD_NAME
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"], skku_cache.CacheResource.POST_LIST
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["key"], {"offset": 10, "limit": 5}
        )
        self.assertEqual(items[0].key.type, "skku_article")
        self.assertEqual(items[0].key.article_no, 219037)

    async def test_skb_detail_uses_cache_namespace_and_article_key(self) -> None:
        fetch_html = AsyncMock(return_value=SKB_DETAIL_HTML)

        with (
            patch(
                "crawl_skku.article.skb_swuniv.service.skku_service.fetch_html",
                fetch_html,
            ),
            patch(
                "crawl_skku.article.skb_swuniv.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            detail = await SkbSwunivArticlePostService().get_post(article_no=219037)

        fetch_html.assert_awaited_once_with(
            skb_constants.BOARD_BASE_URL,
            params={"mode": "view", "articleNo": 219037},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["namespace"], skb_constants.BOARD_NAME
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"],
            skku_cache.CacheResource.POST_DETAIL,
        )
        self.assertEqual(get_or_load.call_args.kwargs["key"], {"article_no": 219037})
        self.assertEqual(detail.key.type, "skku_article")
        self.assertEqual(detail.key.article_no, 219037)

    async def test_cse_list_uses_cache_namespace_and_offset_key(self) -> None:
        fetch_html = AsyncMock(return_value=CSE_LIST_HTML)

        with (
            patch("crawl_skku.article.cse.service.skku_service.fetch_html", fetch_html),
            patch(
                "crawl_skku.article.cse.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            items = await CseArticlePostService().get_posts(offset=10, limit=5)

        fetch_html.assert_awaited_once_with(
            cse_constants.BOARD_BASE_URL,
            params={"article.offset": 10, "articleLimit": 5},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["namespace"], cse_constants.BOARD_NAME
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"], skku_cache.CacheResource.POST_LIST
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["key"], {"offset": 10, "limit": 5}
        )
        self.assertEqual(items[0].key.type, "skku_article")
        self.assertEqual(items[0].key.article_no, 218999)

    async def test_cse_detail_uses_cache_namespace_and_article_key(self) -> None:
        fetch_html = AsyncMock(return_value=CSE_DETAIL_HTML)

        with (
            patch("crawl_skku.article.cse.service.skku_service.fetch_html", fetch_html),
            patch(
                "crawl_skku.article.cse.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            detail = await CseArticlePostService().get_post(article_no=219187)

        fetch_html.assert_awaited_once_with(
            cse_constants.BOARD_BASE_URL,
            params={"mode": "view", "articleNo": 219187},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["namespace"], cse_constants.BOARD_NAME
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"],
            skku_cache.CacheResource.POST_DETAIL,
        )
        self.assertEqual(get_or_load.call_args.kwargs["key"], {"article_no": 219187})
        self.assertEqual(detail.key.type, "skku_article")
        self.assertEqual(detail.key.article_no, 219187)

    async def test_sco_list_uses_cache_namespace_and_offset_key(self) -> None:
        fetch_html = AsyncMock(return_value=SCO_LIST_HTML)

        with (
            patch("crawl_skku.article.sco.service.skku_service.fetch_html", fetch_html),
            patch(
                "crawl_skku.article.sco.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            items = await ScoArticlePostService().get_posts(offset=10, limit=5)

        fetch_html.assert_awaited_once_with(
            sco_constants.BOARD_BASE_URL,
            params={"article.offset": 10, "articleLimit": 5},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["namespace"], sco_constants.BOARD_NAME
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"], skku_cache.CacheResource.POST_LIST
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["key"], {"offset": 10, "limit": 5}
        )
        self.assertEqual(items[0].key.type, "skku_article")
        self.assertEqual(items[0].key.article_no, 218813)

    async def test_sco_detail_uses_cache_namespace_and_article_key(self) -> None:
        fetch_html = AsyncMock(return_value=SCO_DETAIL_HTML)

        with (
            patch("crawl_skku.article.sco.service.skku_service.fetch_html", fetch_html),
            patch(
                "crawl_skku.article.sco.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            detail = await ScoArticlePostService().get_post(article_no=218858)

        fetch_html.assert_awaited_once_with(
            sco_constants.BOARD_BASE_URL,
            params={"mode": "view", "articleNo": 218858},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["namespace"], sco_constants.BOARD_NAME
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"],
            skku_cache.CacheResource.POST_DETAIL,
        )
        self.assertEqual(get_or_load.call_args.kwargs["key"], {"article_no": 218858})
        self.assertEqual(detail.key.type, "skku_article")
        self.assertEqual(detail.key.article_no, 218858)


if __name__ == "__main__":
    unittest.main()
