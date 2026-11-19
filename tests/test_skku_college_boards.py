import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, call, patch

from httpx import ASGITransport, AsyncClient

from crawl_skku import CrawlSkkuClient
from crawl_skku.api import app
from crawl_skku.article.college_sources import (
    INTEGRATED_COLLEGE_BOARDS,
    NUMBERED_COLLEGE_BOARDS,
)
from crawl_skku.cache.config import SkkuCacheSettings
from crawl_skku.exceptions import SkkuParseError

INTEGRATED_SOURCES = (
    "art",
    "biotech",
    "coe",
    "hakbu",
    "ics",
    "liberalarts",
    "scos",
    "sport",
    "sscience",
)
NUMBERED_SOURCES = ("biz", "ecostat", "pharm")


def cms_list(*numbers: int, integrated: bool = False, pinned: int = 0) -> str:
    rows = []
    for index, number in enumerate(numbers):
        query = (
            f"viewBoardId=123&amp;itemId=synthetic-{number}"
            if integrated
            else f"articleNo={number}"
        )
        top = "board-list-content-top" if index < pinned else ""
        rows.append(f"""
        <li>
          <div class="board-list-content-title {top}">
            <span class="c-board-list-category">[학사]</span>
            <a href="?mode=view&amp;{query}">Synthetic {number}</a>
          </div>
          <div class="board-list-content-info">
            <ul><li>No.55</li><li>Test office</li><li>2026-03-02 17:01</li></ul>
          </div>
          <div class="board-list-etc-wrap"><i class="c-board-file-icon"></i></div>
        </li>
        """)
    return f'<ul class="board-list-wrap">{"".join(rows)}</ul>'


CMS_DETAIL = """
<div class="board-view-box">
  <div class="board-view-title-wrap">
    <h4><span class="c-board-view-category">[학사]</span> Synthetic title</h4>
    <ul class="board-etc-wrap"><li>Test office</li><li>조회수 42</li>
      <li>2026-03-02 17:01</li></ul>
  </div>
  <div class="board-view-file-wrap">
    <a href="https://files.example.test/downloadFile.do?fileId=test">Schedule.pdf</a>
  </div>
  <div class="board-view-content-wrap">
    <img src="/test/notice.png" alt="Poster.png">
    <img src="/test/notice.png">
    <img src="data:image/png;base64,test">
    <script>discard()</script>
  </div>
</div>
"""

PHARM_DETAIL = """
<section id="bo_view">
  <header>
    <h1>Synthetic pharmacy title</h1>
    <span class="cate">학부</span><span class="write">Test office</span>
    <span class="time">등록일 26-03-02</span>
  </header>
  <div class="bo_file"><a href="./download.php?no=0">Test.pdf</a></div>
  <article class="new_contents"><div id="bo_v_con"><p>Synthetic body</p></div></article>
</section>
"""


def pharm_list(numbers: range) -> str:
    rows = [
        f"""
        <li><a href="//pharm.skku.edu/bbs/board.php?bo_table=notice&amp;wr_id={number}">
          <article class="bo_info">
            <h2><span class="category">공지</span> Synthetic {number}</h2>
            <span class="write">Test office</span><span class="time">2026-03-02</span>
            <span class="lst_file">첨부파일</span>
          </article>
        </a></li>
        """
        for number in numbers
    ]
    return f'<ol id="board_list">{"".join(rows)}</ol>'


class CollegeBoardTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = self.enterContext(
            patch(
                "crawl_skku.cache.get_cache_settings",
                return_value=SkkuCacheSettings(enabled=False),
            )
        )
        self.fetch = self.enterContext(
            patch("crawl_skku.service.fetch_html", new_callable=AsyncMock)
        )
        self.client = CrawlSkkuClient()

    async def test_integrated_window_crosses_upstream_page_boundary(self) -> None:
        url = INTEGRATED_COLLEGE_BOARDS["hakbu"].url
        self.fetch.side_effect = [
            cms_list(3, 4, integrated=True),
            cms_list(5, integrated=True),
        ]

        rows = await self.client.get_posts("hakbu", offset=3, limit=2)

        self.assertEqual([row.title for row in rows], ["Synthetic 4", "Synthetic 5"])
        self.assertEqual(
            rows[0].key.model_dump(),
            {"type": "skku_article", "board_id": 123, "item_id": "synthetic-4"},
        )
        self.assertEqual(rows[0].category, "학사")
        self.assertEqual(rows[0].author, "Test office")
        self.assertEqual(rows[0].date, date(2026, 3, 2))
        self.assertTrue(rows[0].has_attachment)
        self.assertEqual(
            self.fetch.await_args_list,
            [
                call(url, params={"article.offset": 2, "articleLimit": 2}),
                call(url, params={"article.offset": 4, "articleLimit": 2}),
            ],
        )

    async def test_numbered_window_counts_pinned_posts_once(self) -> None:
        self.fetch.side_effect = [
            cms_list(90, 91, 3, 4, pinned=2),
            cms_list(90, 91, 1, 2, pinned=2),
        ]

        rows = await self.client.get_posts("biz", offset=3, limit=2)

        self.assertEqual([row.key.article_no for row in rows], [2, 3])
        self.assertEqual(
            [
                args.kwargs["params"]["article.offset"]
                for args in self.fetch.await_args_list
            ],
            [2, 0],
        )

    async def test_pharmacy_window_spans_pages_without_losing_pinned_rows(self) -> None:
        self.fetch.side_effect = [pharm_list(range(1, 11)), pharm_list(range(11, 13))]
        rows = await self.client.get_posts("pharm", offset=9, limit=5)
        self.assertEqual([row.key.article_no for row in rows], [10, 11, 12])
        self.assertEqual(rows[0].title, "Synthetic 10")
        self.assertEqual(
            [args.kwargs["params"] for args in self.fetch.await_args_list],
            [{"bo_table": "notice", "page": 1}, {"bo_table": "notice", "page": 2}],
        )

    async def test_sqlite_cache_round_trips_lists_and_details_per_source(self) -> None:
        with TemporaryDirectory() as tmp:
            self.settings.return_value = SkkuCacheSettings(cache_dir=Path(tmp))
            self.fetch.side_effect = [
                cms_list(1, integrated=True),
                CMS_DETAIL,
                cms_list(2, integrated=True),
                CMS_DETAIL,
            ]

            first = await self.client.get_posts("hakbu", limit=1)
            hakbu = await self.client.get_integrated_post("hakbu", 123, "synthetic-1")
            second = await self.client.get_posts("art", limit=1)
            art = await self.client.get_integrated_post("art", 123, "synthetic-1")
            self.assertEqual(first, await self.client.get_posts("hakbu", limit=1))
            self.assertEqual(second, await self.client.get_posts("art", limit=1))
            self.assertEqual(
                hakbu,
                await self.client.get_integrated_post("hakbu", 123, "synthetic-1"),
            )
            self.assertEqual(
                art, await self.client.get_integrated_post("art", 123, "synthetic-1")
            )

        self.assertEqual(self.fetch.await_count, 4)
        self.assertNotEqual(first[0].key, second[0].key)
        self.assertNotEqual(hakbu.url, art.url)
        self.assertEqual(hakbu.description, "")
        self.assertEqual(
            [attachment.file_format for attachment in hakbu.attachments or []],
            ["pdf", "png"],
        )

    async def test_empty_board_and_invalid_markup_are_distinct(self) -> None:
        self.fetch.side_effect = [
            '<ul class="board-list-wrap"><li>등록된 글이 없습니다.</li></ul>',
            '<ol id="board_list"><li class="no_data">등록된 글이 없습니다.</li></ol>',
            "<html></html>",
        ]
        self.assertEqual(await self.client.get_posts("art"), [])
        self.assertEqual(await self.client.get_posts("pharm"), [])
        with self.assertRaises(SkkuParseError):
            await self.client.get_posts("art")

    async def test_integrated_pagination_does_not_replay_last_page(self) -> None:
        self.fetch.return_value = (
            cms_list(3, integrated=True)
            + """
            <ul class="paging-wrap">
              <li><a class="page-last" href="?article.offset=2">Last page</a></li>
            </ul>
        """
        )
        self.assertEqual(await self.client.get_posts("hakbu", offset=4, limit=2), [])

    def test_openapi_lists_every_source_with_its_actual_detail_key(self) -> None:
        paths = app.openapi()["paths"]
        self.assertCountEqual(INTEGRATED_COLLEGE_BOARDS, INTEGRATED_SOURCES)
        self.assertCountEqual(NUMBERED_COLLEGE_BOARDS, NUMBERED_SOURCES)
        for source in (*INTEGRATED_SOURCES, *NUMBERED_SOURCES):
            with self.subTest(source=source):
                base = f"/skku/article/{source}/posts"
                suffix = (
                    "/{board_id}/{item_id}"
                    if source in INTEGRATED_SOURCES
                    else "/{article_no}"
                )
                self.assertEqual(
                    paths[base]["get"]["tags"], [f"SKKU {source.upper()} posts"]
                )
                self.assertIn(base + suffix, paths)

    async def test_api_lists_and_gets_posts_for_all_added_sources(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as http:
            for source in (*INTEGRATED_SOURCES, *NUMBERED_SOURCES):
                with self.subTest(source=source):
                    integrated = source in INTEGRATED_SOURCES
                    pharm = source == "pharm"
                    self.fetch.reset_mock()
                    self.fetch.side_effect = [
                        pharm_list(range(1, 2))
                        if pharm
                        else cms_list(1, integrated=integrated),
                        PHARM_DETAIL if pharm else CMS_DETAIL,
                    ]
                    base = f"/skku/article/{source}/posts"
                    resp = await http.get(base, params={"limit": 1})
                    self.assertEqual(resp.status_code, 200)
                    key = resp.json()[0]["key"]
                    suffix = (
                        f"{key['board_id']}/{key['item_id']}"
                        if integrated
                        else str(key["article_no"])
                    )
                    resp = await http.get(f"{base}/{suffix}")
                    self.assertEqual(resp.status_code, 200)
                    self.assertEqual(resp.json()["key"], key)
                    self.assertEqual(resp.json()["date"], "2026-03-02")
                    self.assertEqual(
                        resp.json()["category"], "학부" if pharm else "학사"
                    )
                    self.assertEqual(
                        self.fetch.await_args.kwargs["params"],
                        {"bo_table": "notice", "wr_id": 1}
                        if pharm
                        else {
                            "mode": "view",
                            "viewBoardId": 123,
                            "itemId": "synthetic-1",
                        }
                        if integrated
                        else {"mode": "view", "articleNo": 1},
                    )

    async def test_invalid_params_and_upstream_errors_map_to_http_errors(self) -> None:
        self.fetch.return_value = "<html></html>"
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as http:
            self.assertEqual(
                (await http.get("/skku/article/hakbu/posts?limit=0")).status_code, 422
            )
            self.assertEqual(
                (await http.get("/skku/article/hakbu/posts/0/test")).status_code, 422
            )
            self.assertEqual(
                (await http.get("/skku/article/hakbu/posts/1")).status_code, 404
            )
            self.fetch.assert_not_awaited()
            self.assertEqual(
                (await http.get("/skku/article/hakbu/posts")).status_code, 502
            )
