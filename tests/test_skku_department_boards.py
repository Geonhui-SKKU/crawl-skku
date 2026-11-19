import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, call, patch

from httpx import ASGITransport, AsyncClient

from crawl_skku import CrawlSkkuClient
from crawl_skku.api import app
from crawl_skku.article.department_sources import (
    NUMBERED_DEPARTMENT_BOARDS,
    STANDARD_DEPARTMENT_BOARDS,
)
from crawl_skku.cache.config import SkkuCacheSettings
from tests.test_skku_college_boards import CMS_DETAIL, PHARM_DETAIL, cms_list

CHEM_META = """
<ul class="noticeInfoList"><li>POSTED DATE : 2024-01-02</li>
<li>WRITER : Test Office</li><li>HIT : 5</li></ul>
"""
CHEM_LIST = f"""
<ul class="noticeList"><li><h3 class="noticeTit">
<a href="?mode=view&amp;articleNo=41">Chemistry notice</a></h3>{CHEM_META}</li></ul>
"""
CHEM_DETAIL = f"""
<div class="board view"><h3 class="noticeTit">Chemistry notice</h3>{CHEM_META}
<div class="fr-view">Test body</div>
<button class="fileBtn" onclick="location.href='?mode=download&amp;attachNo=5'">Form.pdf</button>
<button class="fileBtn" onclick="unrelated()">Ignore</button>
</div>
"""
BIO_DETAIL = """
<article id="bo_v"><h2 id="bo_v_title">Full biology notice</h2>
<section id="bo_v_info">
  <span class="sv_member">Test Office</span><strong class="if_date">작성일 23-01-02 03:04</strong>
</section>
<div id="bo_v_con">Test body</div>
<section id="bo_v_file"><a href="./download.php?no=0">Form.pdf</a></section>
</article>
"""
CAL_DETAIL = """
<table class="board_Vtable"><thead><tr><th>Civil engineering notice</th></tr>
<tr><td><ul><li>Office</li><li class="imbar">|</li><li>4</li>
<li class="imbar">|</li><li>2024-01-02 03:04:05</li></ul></td></tr></thead>
<tbody><tr><td><div class="board_content">Test body</div></td></tr>
<tr><td><a href="./NFUpload/nfupload_down.php?name=Test+form.pdf">Download</a></td></tr>
</tbody></table>
"""
NANO_LIST = """
<div id="sub_contents"><div class="conbody"><table><tr>
<td class="responsive03"><a href="?tbl=bbs42&amp;mode=VIEW&amp;num=43">Nano notice</a>
<p class="tablet_regist_date">2024-01-02</p>
<p class="mobile_regist_date">Office | 2024-01-02 | 조회수 : 1</p></td>
</tr></table></div></div>
"""
NANO_DETAIL = """
<div class="conbody"><table><tr height="35"><td><strong>Nano notice</strong></td></tr>
<tr><td><ul class="bbs_top">
<li><em>글쓴이</em><span>Office</span></li><li><em>작성일</em><span>2024-01-02</span></li>
</ul></td></tr><tr><td><a href="./download.php?no=17">Form.pdf</a></td></tr>
<tr><td><div id="DivContents">Test body</div></td></tr><tr><td class="viewBtnArea"></td></tr>
</table></div>
"""
DOES_LIST = """
<main><section><form action="/board/notice"></form><ul><li>
<a href="/board/notice/44"><span class="leading-snug">Energy Science notice</span>
<span class="inline-flex"><svg></svg></span><time>2024-01-02</time></a>
</li></ul></section></main>
"""
DOES_DETAIL = """
<main><article><header><h1>Energy Science notice</h1><p class="font-mono">2024-01-02</p></header>
<div class="board-body">Test body</div>
<a href="/files/4"><span>Form.pdf</span><span>17 KB</span></a></article></main>
"""


def cal_list(regular: range, pins: tuple[int, ...] = (81, 82)) -> str:
    rows = []
    for idx in (*pins, *regular):
        label = '<span class="label-warning">공지</span>' if idx in pins else str(idx)
        rows.append(f"""
        <tr><td>{label}</td><td>학사</td>
        <td class="alignLeft"><a href="?page=view&amp;idx={idx}">Test {idx}</a></td>
        <td class="file_a"></td><td>3</td><td>2024-01-02</td></tr>
        """)
    return f'<table class="board_table"><tbody>{"".join(rows)}</tbody></table>'


def biopharm_list(numbers: range) -> str:
    rows = "".join(
        f'<li><a href="?bo_table=notice&amp;wr_id={n}"><div class="bo_info">'
        f'<h2>Test {n}</h2><span class="time">2024-01-02</span></div></a></li>'
        for n in numbers
    )
    return f'<ol id="board_list">{rows}</ol>'


class DepartmentBoardTests(unittest.IsolatedAsyncioTestCase):
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

    def test_openapi_registers_department_boards_and_preserves_cse(self) -> None:
        self.assertEqual(len(STANDARD_DEPARTMENT_BOARDS), 51)
        self.assertEqual(len(NUMBERED_DEPARTMENT_BOARDS), 57)
        paths = app.openapi()["paths"]
        for source in NUMBERED_DEPARTMENT_BOARDS:
            with self.subTest(source=source):
                prefix = f"/skku/article/{source}/posts"
                self.assertIn(prefix, paths)
                self.assertIn(f"{prefix}/{{article_no}}", paths)
        self.assertIn("/skku/article/cse/posts/{article_no}", paths)
        self.assertNotIn("/skku/article/sce/posts", paths)

    async def test_computer_education_uses_its_own_board(self) -> None:
        self.fetch.side_effect = [cms_list(41), CMS_DETAIL]
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as http:
            rows = await http.get("/skku/article/comedu/posts?limit=1")
            detail = await http.get("/skku/article/comedu/posts/41")
        self.assertEqual(rows.status_code, 200)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["key"], rows.json()[0]["key"])
        self.assertEqual(
            [args.args[0] for args in self.fetch.await_args_list],
            ["https://comedu.skku.edu/comedu/notice.do"] * 2,
        )

    async def test_biopharm_translates_fifteen_row_pages(self) -> None:
        self.fetch.side_effect = [
            biopharm_list(range(1, 16)),
            biopharm_list(range(16, 19)),
            PHARM_DETAIL,
        ]
        rows = await self.client.get_posts("biopharm", offset=14, limit=3)
        self.assertEqual([row.key.article_no for row in rows], [15, 16, 17])
        self.assertTrue(rows[0].url.startswith("https://biopharm.skku.edu/"))
        detail = await self.client.get_post("biopharm", 15)
        self.assertTrue(
            detail.attachments[0].url.startswith("https://biopharm.skku.edu/")
        )
        board = "https://biopharm.skku.edu/bbs/board.php"
        self.assertEqual(
            self.fetch.await_args_list,
            [call(board, params={"bo_table": "notice", "page": n}) for n in (1, 2)]
            + [call(board, params={"bo_table": "notice", "wr_id": 15})],
        )

    async def test_distinct_templates_share_the_numbered_api_contract(self) -> None:
        cases = (
            ("chem", CHEM_LIST, CHEM_DETAIL, 41, {"mode": "view", "articleNo": 41}),
            (
                "cal",
                cal_list(range(42, 43), pins=()),
                CAL_DETAIL,
                42,
                {"hCode": "BOARD", "bo_idx": 17, "page": "view", "idx": 42},
            ),
            (
                "nano",
                NANO_LIST,
                NANO_DETAIL,
                43,
                {"tbl": "bbs42", "mode": "VIEW", "num": 43},
            ),
            ("does", DOES_LIST, DOES_DETAIL, 44, {}),
        )
        for source, list_html, detail_html, article_no, params in cases:
            with self.subTest(source=source):
                self.fetch.reset_mock(side_effect=True)
                self.fetch.side_effect = [list_html, detail_html]
                rows = await self.client.get_posts(source, limit=1)
                detail = await self.client.get_post(source, rows[0].key.article_no)
                self.assertEqual(rows[0].key.article_no, article_no)
                self.assertEqual(detail.key, rows[0].key)
                self.assertEqual(detail.date, date(2024, 1, 2))
                self.assertEqual(detail.description, "Test body")
                files = detail.attachments or []
                self.assertEqual(len(files), 1)
                self.assertEqual(files[0].file_format, "pdf")
                self.assertEqual(
                    files[0].name, "Test form.pdf" if source == "cal" else "Form.pdf"
                )
                self.assertEqual(self.fetch.await_args.kwargs["params"], params)
                if source == "does":
                    self.assertEqual(
                        detail.url, "https://does.skku.edu/board/notice/44"
                    )

    async def test_cal_repeated_pinned_prefix_does_not_reset_offset(self) -> None:
        self.fetch.side_effect = [cal_list(range(1, 21)), cal_list(range(21, 41))]
        posts = await self.client.get_posts("cal", offset=21, limit=3)
        self.assertEqual([row.key.article_no for row in posts], [20, 21, 22])
        self.assertEqual(
            [c.kwargs["params"]["pg"] for c in self.fetch.await_args_list], [1, 2]
        )

    async def test_chem_empty_page_marker_is_not_a_post(self) -> None:
        self.fetch.return_value = '<ul class="noticeList"><li><h3 class="noticeTit">No new posts.</h3></li></ul>'
        self.assertEqual(await self.client.get_posts("chem", offset=10), [])

    async def test_biology_only_fetches_selected_details_and_preserves_year(
        self,
    ) -> None:
        self.fetch.side_effect = [
            "<div id='bo_list'><table><tbody><tr><td>"
            "<a href='?wr_id=45'>Truncated title…</a><a href='?wr_id=46'>Skip</a>"
            "</td><td>01-02</td></tr></tbody></table></div>",
            BIO_DETAIL,
        ]
        with TemporaryDirectory() as tmp:
            self.settings.return_value = SkkuCacheSettings(cache_dir=Path(tmp))
            rows = await self.client.get_posts("bio", limit=1)
            detail = await self.client.get_post("bio", 45)
            self.assertEqual(await self.client.get_posts("bio", limit=1), rows)
        self.assertEqual(rows[0].date, date(2023, 1, 2))
        self.assertEqual(rows[0].title, "Full biology notice")
        self.assertEqual(detail.key, rows[0].key)
        self.assertEqual(self.fetch.await_count, 2)
