import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from crawl_skku import cache as skku_cache
from crawl_skku.article.root import constants
from crawl_skku.article.root.service import RootArticlePostService
from crawl_skku.cache import SkkuCacheSettings

SERVICE_LIST_HTML = """
<ul class="board-list-wrap">
  <li>
    <dl>
      <dt class="board-list-content-title">
        <a href="?mode=view&amp;articleNo=101">First post</a>
      </dt>
      <dd class="board-list-content-info">
        <ul><li>No.1</li><li>Admin</li><li>2031-02-14</li></ul>
      </dd>
    </dl>
  </li>
  <li>
    <dl>
      <dt class="board-list-content-title">
        <a href="?mode=view&amp;articleNo=102">Second post</a>
      </dt>
      <dd class="board-list-content-info">
        <ul><li>No.2</li><li>Admin</li><li>2031-02-13</li></ul>
      </dd>
    </dl>
  </li>
  <li>
    <dl>
      <dt class="board-list-content-title">
        <a href="?mode=view&amp;articleNo=103">Third post</a>
      </dt>
      <dd class="board-list-content-info">
        <ul><li>No.3</li><li>Admin</li><li>2031-02-12</li></ul>
      </dd>
    </dl>
  </li>
</ul>
"""

SERVICE_DETAIL_HTML = """
<table class="board_view">
  <thead>
    <tr>
      <th>
        <span class="category">[학사]</span>
        <em class="ellipsis">Detail post</em>
        <span class="date">최종 수정일 : 2031.02.14</span>
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <div class="boardView_txtWrap">
          <div class="flL">
            <ul class="boardView_txtList"><li>Admin</li></ul>
          </div>
        </div>
        <dl class="board-write-box"><dd>Detail body</dd></dl>
      </td>
    </tr>
  </tbody>
</table>
"""


class SkkuRootArticleServiceTests(unittest.IsolatedAsyncioTestCase):
    def make_cache_settings(self) -> SkkuCacheSettings:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        return SkkuCacheSettings(cache_dir=Path(self.tempdir.name))

    async def test_get_posts_applies_offset_and_limit(self) -> None:
        fetch_html = AsyncMock(return_value=SERVICE_LIST_HTML)

        with (
            patch(
                "crawl_skku.article.root.service.skku_service.fetch_html", fetch_html
            ),
            patch(
                "crawl_skku.article.root.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            items = await RootArticlePostService().get_posts(offset=2, limit=2)

        fetch_html.assert_awaited_once_with(
            constants.BOARD_BASE_URL,
            params={"article.offset": 2, "articleLimit": 2},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"], skku_cache.CacheResource.POST_LIST
        )
        self.assertEqual(get_or_load.call_args.kwargs["key"], {"offset": 2, "limit": 2})
        self.assertEqual(
            [item.key.type for item in items], ["skku_article", "skku_article"]
        )
        self.assertEqual([item.key.article_no for item in items], [101, 102])

    async def test_get_post_uses_detail_cache_key(self) -> None:
        fetch_html = AsyncMock(return_value=SERVICE_DETAIL_HTML)

        with (
            patch(
                "crawl_skku.article.root.service.skku_service.fetch_html", fetch_html
            ),
            patch(
                "crawl_skku.article.root.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            item = await RootArticlePostService().get_post(article_no=137564)

        fetch_html.assert_awaited_once_with(
            constants.BOARD_BASE_URL,
            params={"mode": "view", "articleNo": 137564},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"],
            skku_cache.CacheResource.POST_DETAIL,
        )
        self.assertEqual(get_or_load.call_args.kwargs["key"], {"article_no": 137564})
        self.assertEqual(item.key.type, "skku_article")
        self.assertEqual(item.key.article_no, 137564)

    async def test_get_posts_reuses_enabled_cache(self) -> None:
        fetch_html = AsyncMock(return_value=SERVICE_LIST_HTML)
        settings = self.make_cache_settings()

        async def run_sync_inline(func, *args, **kwargs):
            return func(*args, **kwargs)

        with (
            patch(
                "crawl_skku.article.root.service.skku_service.fetch_html", fetch_html
            ),
            patch("crawl_skku.cache.get_cache_settings", return_value=settings),
            patch("crawl_skku.cache.service.run_in_threadpool", new=run_sync_inline),
        ):
            first = await RootArticlePostService().get_posts(offset=0, limit=2)
            second = await RootArticlePostService().get_posts(offset=0, limit=2)

        fetch_html.assert_awaited_once()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
