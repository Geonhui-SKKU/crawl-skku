import unittest
from datetime import date

from crawl_skku.article.enc import constants as enc_constants
from crawl_skku.article.enc import utils as enc_utils
from crawl_skku.article.ice import constants as ice_constants
from crawl_skku.article.ice import utils as ice_utils

LIST_HTML = """
<ul class="board-list-wrap">
  <li>
    <dl>
      <dt class="board-list-content-title">
        <a href="?mode=view&amp;articleNo=226064">Synthetic notice</a>
      </dt>
      <dd class="board-list-content-info"><ul>
        <li>No.1023</li><li>Example College</li><li>2031-02-12</li>
      </ul></dd>
    </dl>
    <div class="board-list-etc-wrap"><span class="board-list-file"></span></div>
  </li>
</ul>
"""

DETAIL_HTML = """
<div class="board-view-box">
  <div class="board-view-title-wrap">
    <h4>Synthetic notice</h4>
    <ul class="board-etc-wrap">
      <li>Example College</li><li>조회수 12</li><li>2031-02-12</li>
    </ul>
  </div>
  <ul class="board-view-file-wrap">
    <li><a href="?mode=download&amp;articleNo=226064">notice.pdf</a></li>
  </ul>
  <div class="board-view-content-wrap">Synthetic description</div>
</div>
"""

ENC_CURRENT_LIST_HTML = """
<ul class="board-list-wrap">
  <li><dl>
    <dt class="board-list-content-title">
      <span class="c-board-list-category">[행사/세미나]</span>
      <a href="?mode=view&amp;link=null&amp;viewBoardId=138885&amp;itemId=ABC123&amp;article.offset=0&amp;articleLimit=10">Current ENC notice</a>
    </dt>
    <dd class="board-list-content-info"><ul>
      <li>No.1717</li><li>공과대학</li><li>2026-09-23 10:52</li>
    </ul></dd>
  </dl><div class="board-list-etc-wrap"><ul>
    <li class="c-board-file-icon board-list-file">첨부파일</li>
  </ul></div></li>
</ul>
"""

ENC_CURRENT_DETAIL_HTML = """
<div class="board-view-box">
  <div class="board-view-title-wrap">
    <h4><span>[행사/세미나]</span>Current ENC notice</h4>
    <ul class="board-etc-wrap"><li>공과대학</li><li>2026-09-23 10:52</li></ul>
  </div>
  <ul class="board-view-file-wrap">
    <li><a class="file-down-btn" href="https://portal.skku.edu/support/fileupload/downloadFile.do?fileId=XYZ">notice.hwp</a></li>
  </ul>
  <div class="board-view-content-wrap">Current description</div>
</div>
"""


class SkkuEncIceParserTests(unittest.TestCase):
    def test_enc_parses_current_item_id_links(self) -> None:
        item = enc_utils.parse_post_list(ENC_CURRENT_LIST_HTML)[0]
        detail = enc_utils.parse_post_detail(
            ENC_CURRENT_DETAIL_HTML, article_no=1717, board_id=138885, item_id="ABC123"
        )

        self.assertEqual(item.key.article_no, 1717)
        self.assertEqual(
            item.key.model_extra, {"board_id": 138885, "item_id": "ABC123"}
        )
        self.assertEqual(item.category, "행사/세미나")
        self.assertEqual(item.date, date(2026, 9, 23))
        self.assertTrue(item.has_attachment)
        self.assertEqual(detail.key, item.key)
        self.assertEqual(
            detail.url, enc_constants.build_item_detail_url(138885, "ABC123")
        )
        self.assertEqual((detail.attachments or [])[0].name, "notice.hwp")
        self.assertEqual((detail.attachments or [])[0].file_format, "hwp")

    def test_parsers_use_their_source_urls(self) -> None:
        for utils, constants in (
            (enc_utils, enc_constants),
            (ice_utils, ice_constants),
        ):
            item = utils.parse_post_list(LIST_HTML)[0]
            detail = utils.parse_post_detail(DETAIL_HTML, article_no=226064)

            self.assertEqual(item.key.article_no, 226064)
            self.assertEqual(item.author, "Example College")
            self.assertEqual(item.date, date(2031, 2, 12))
            self.assertTrue(item.has_attachment)
            self.assertEqual(detail.url, constants.build_detail_url(226064))
            self.assertEqual(
                (detail.attachments or [])[0].url,
                constants.build_detail_url(226064).replace(
                    "mode=view", "mode=download"
                ),
            )


if __name__ == "__main__":
    unittest.main()
