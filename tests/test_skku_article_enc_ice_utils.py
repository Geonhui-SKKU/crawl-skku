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


class SkkuEncIceParserTests(unittest.TestCase):
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
