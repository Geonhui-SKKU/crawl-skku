import unittest
from datetime import date

from crawl_skku.article.cscience import constants, utils

ITEM_ID = "74F853B3B1A0AC969CF13224382D14CFVHNIHP"

LIST_HTML = f"""
<ul class="board-list-wrap">
  <li>
    <dl>
      <dt class="board-list-content-title">
        <span class="c-board-list-category">[학사]</span>
        <a href="?mode=view&amp;viewBoardId=138879&amp;itemId={ITEM_ID}">
          Synthetic CScience notice
        </a>
      </dt>
      <dd class="board-list-content-info"><ul>
        <li>No.809</li><li>Natural Sciences College</li><li>2031-02-12 12:34</li>
      </ul></dd>
    </dl>
  </li>
</ul>
"""

DETAIL_HTML = """
<div class="board-view-box">
  <div class="board-view-title-wrap">
    <h4>Synthetic CScience notice</h4>
    <ul class="board-etc-wrap">
      <li>Natural Sciences College</li><li>조회수 12</li><li>2031-02-12</li>
    </ul>
  </div>
  <div class="board-view-content-wrap">Synthetic description</div>
</div>
"""


class SkkuCscienceParserTests(unittest.TestCase):
    def test_parse_posts_with_source_specific_key(self) -> None:
        item = utils.parse_post_list(LIST_HTML)[0]
        detail = utils.parse_post_detail(
            DETAIL_HTML,
            board_id=138879,
            item_id=ITEM_ID,
        )

        self.assertEqual(item.key.type, "cscience_article")
        self.assertEqual(item.key.board_id, 138879)
        self.assertEqual(item.key.item_id, ITEM_ID)
        self.assertEqual(item.category, "학사")
        self.assertEqual(item.date, date(2031, 2, 12))
        self.assertEqual(detail.url, constants.build_detail_url(138879, ITEM_ID))


if __name__ == "__main__":
    unittest.main()
