import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, call, patch
from urllib.parse import urljoin

from httpx import ASGITransport, AsyncClient

from crawl_skku import CrawlSkkuClient
from crawl_skku.api import app
from crawl_skku.cache.config import SkkuCacheSettings

BOARD_URL = "https://aiuniv.skku.edu/aiuniv/notice.do"

LIST_HTML = """
<ul class="board-list-wrap">
  <li>
    <dl>
      <dt class="board-list-content-title">
        <a href="?mode=view&amp;articleNo=219037&amp;article.offset=0&amp;articleLimit=10">
          Synthetic mentor program enrollment
        </a>
      </dt>
      <dd class="board-list-content-info">
        <ul>
          <li>No.270</li>
          <li>Example Program Office</li>
          <li>2031-02-12</li>
          <li>조회수<span>302</span></li>
        </ul>
      </dd>
    </dl>
    <div class="board-list-etc-wrap">
      <ul><li class="c-board-file-icon board-list-file"><span>첨부파일</span></li></ul>
    </div>
  </li>
</ul>
"""


DETAIL_HTML = """
<div class="board-view-box">
  <div class="board-view-title-wrap">
    <h4>Synthetic mentor program enrollment</h4>
    <ul class="board-etc-wrap">
      <li>Example Program Office</li>
      <li>조회수<span>302</span></li>
      <li>2031-02-12</li>
    </ul>
  </div>
  <ul class="board-view-file-wrap">
    <li>
      <a class="file-down-btn docx" href="?mode=download&amp;articleNo=219037&amp;attachNo=193986">
        synthetic-mentor-guide.docx
      </a>
    </li>
    <li>
      <a class="file-down-btn docx" href="?mode=download&amp;articleNo=219037&amp;attachNo=193987">
        synthetic-mentor-details.docx
      </a>
    </li>
  </ul>
  <div class="board-view-content-wrap board-view-txt">
    <div class="fr-view">
      <ul><li>This is a synthetic mentor program description.</li></ul>
    </div>
  </div>
</div>
"""


DETAIL_WITH_INLINE_IMAGE_HTML = """
<div class="board-view-box">
  <div class="board-view-title-wrap">
    <h4>인라인 이미지 안내</h4>
    <ul class="board-etc-wrap">
      <li>Example Program Office</li>
      <li>조회수<span>302</span></li>
      <li>2031-02-12</li>
    </ul>
  </div>
  <ul class="board-view-file-wrap"></ul>
  <div class="board-view-content-wrap board-view-txt">
    <div class="fr-view">
      <p>Synthetic body text.</p>
      <img src="/_attach/image/2031/02/sample-poster.jpg" />
    </div>
  </div>
</div>
"""


class AiunivArticleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.fetch = self.enterContext(
            patch("crawl_skku.service.fetch_html", new_callable=AsyncMock)
        )
        self.settings = self.enterContext(
            patch(
                "crawl_skku.cache.get_cache_settings",
                return_value=SkkuCacheSettings(enabled=False),
            )
        )
        self.client = CrawlSkkuClient()

    async def test_parse_post_list(self) -> None:
        self.fetch.return_value = LIST_HTML
        items = await self.client.get_posts("aiuniv", offset=10, limit=5)

        self.fetch.assert_awaited_once_with(
            BOARD_URL, params={"article.offset": 10, "articleLimit": 5}
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].key.type, "skku_article")
        self.assertEqual(items[0].key.article_no, 219037)
        self.assertIsNone(items[0].category)
        self.assertEqual(items[0].date, date(2031, 2, 12))
        self.assertEqual(items[0].author, "Example Program Office")
        self.assertTrue(items[0].has_attachment)
        self.assertTrue(items[0].url.startswith(BOARD_URL))

    async def test_parse_post_detail(self) -> None:
        self.fetch.return_value = DETAIL_HTML
        detail = await self.client.get_post("aiuniv", article_no=219037)

        self.fetch.assert_awaited_once_with(
            BOARD_URL, params={"mode": "view", "articleNo": 219037}
        )
        self.assertEqual(detail.key.type, "skku_article")
        self.assertEqual(detail.key.article_no, 219037)
        self.assertIsNone(detail.category)
        self.assertEqual(
            detail.title,
            "Synthetic mentor program enrollment",
        )
        self.assertEqual(detail.date, date(2031, 2, 12))
        self.assertEqual(detail.author, "Example Program Office")
        self.assertTrue(detail.has_attachment)
        self.assertEqual(len(detail.attachments or []), 2)
        self.assertEqual((detail.attachments or [])[0].file_format, "docx")
        self.assertTrue((detail.attachments or [])[0].url.startswith(BOARD_URL))
        self.assertIn("synthetic mentor", detail.description)

    async def test_parse_post_detail_with_inline_image_attachment(self) -> None:
        self.fetch.return_value = DETAIL_WITH_INLINE_IMAGE_HTML
        detail = await self.client.get_post("aiuniv", article_no=219038)

        self.assertTrue(detail.has_attachment)
        self.assertEqual(len(detail.attachments or []), 1)
        attachment = (detail.attachments or [])[0]
        self.assertEqual(attachment.name, "sample-poster.jpg")
        self.assertEqual(attachment.file_format, "jpg")
        self.assertEqual(
            attachment.url,
            urljoin(BOARD_URL, "/_attach/image/2031/02/sample-poster.jpg"),
        )
        self.assertEqual(detail.description, "Synthetic body text.")

    async def test_legacy_routes_and_client_share_new_upstream_cache(self) -> None:
        self.fetch.side_effect = [LIST_HTML, DETAIL_HTML]
        with TemporaryDirectory() as tmp:
            self.settings.return_value = SkkuCacheSettings(cache_dir=Path(tmp))
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as http:
                canonical = "/skku/article/aiuniv/posts"
                legacy = "/skku/article/skb_swuniv/posts"
                for suffix in ("", "/219037"):
                    new = await http.get(canonical + suffix)
                    old = await http.get(legacy + suffix)
                    self.assertEqual(new.status_code, 200)
                    self.assertEqual(old.status_code, 200)
                    self.assertEqual(old.json(), new.json())
            self.assertEqual(
                await self.client.get_posts("skb_swuniv"),
                await self.client.get_posts("aiuniv"),
            )
            self.assertEqual(
                await self.client.get_post("skb_swuniv", 219037),
                await self.client.get_post("aiuniv", 219037),
            )
        self.assertEqual(
            self.fetch.await_args_list,
            [
                call(BOARD_URL, params={"article.offset": 0, "articleLimit": 10}),
                call(BOARD_URL, params={"mode": "view", "articleNo": 219037}),
            ],
        )


if __name__ == "__main__":
    unittest.main()
