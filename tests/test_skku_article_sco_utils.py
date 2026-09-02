import unittest
from datetime import date

from crawl_skku.article.sco import utils

LIST_HTML = """
<ul class="board-list-wrap">
  <li>
    <dl>
      <dt class="board-list-content-title board-list-content-top">
        <span class="c-board-list-category">[학사]</span>
        <a href="?mode=view&amp;articleNo=218813&amp;article.offset=0&amp;articleLimit=10">
          Synthetic program application notice
        </a>
      </dt>
      <dd class="board-list-content-info">
        <ul>
          <li>공지</li>
          <li>Example School</li>
          <li>2031-02-08</li>
          <li>조회수<span>565</span></li>
        </ul>
      </dd>
    </dl>
    <div class="board-list-etc-wrap">
      <ul><li class="c-board-file-icon board-list-file"><span>첨부파일</span></li></ul>
    </div>
  </li>
  <li>
    <dl>
      <dt class="board-list-content-title">
        <span class="c-board-list-category">[장학]</span>
        <a href="?mode=view&amp;articleNo=218858&amp;article.offset=0&amp;articleLimit=10">
          [Example Initiative] Synthetic challenge registration
        </a>
      </dt>
      <dd class="board-list-content-info">
        <ul>
          <li>No.744</li>
          <li>Example School</li>
          <li>2031-02-09</li>
          <li>조회수<span>259</span></li>
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
    <h4><span>[장학]</span>[Example Initiative] Synthetic challenge registration</h4>
    <ul class="board-etc-wrap">
      <li>Example School</li>
      <li>조회수<span>259</span></li>
      <li>2031-02-09</li>
    </ul>
  </div>
  <ul class="board-view-file-wrap">
    <li>
      <a class="file-down-btn pdf" href="?mode=download&amp;articleNo=218858&amp;attachNo=193735">
        synthetic-challenge-plan.pdf
      </a>
    </li>
    <li>
      <a class="file-down-btn xlsx" href="?mode=download&amp;articleNo=218858&amp;attachNo=193736">
        synthetic-challenge-form.xlsx
      </a>
    </li>
  </ul>
  <div class="board-view-content-wrap board-view-txt">
    <div class="fr-view">
      <pre class="pre">This is a synthetic challenge description.</pre>
    </div>
  </div>
</div>
"""


class SkkuScoParserTests(unittest.TestCase):
    def test_parse_post_list(self) -> None:
        items = utils.parse_post_list(LIST_HTML)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].key.type, "skku_article")
        self.assertEqual(items[0].key.article_no, 218813)
        self.assertEqual(items[0].category, "학사")
        self.assertEqual(items[0].date, date(2031, 2, 8))
        self.assertEqual(items[0].author, "Example School")
        self.assertTrue(items[0].has_attachment)
        self.assertEqual(items[1].key.article_no, 218858)
        self.assertEqual(items[1].category, "장학")
        self.assertTrue(items[1].has_attachment)

    def test_parse_post_detail_with_attachments(self) -> None:
        detail = utils.parse_post_detail(DETAIL_HTML, article_no=218858)

        self.assertEqual(detail.key.type, "skku_article")
        self.assertEqual(detail.key.article_no, 218858)
        self.assertEqual(detail.category, "장학")
        self.assertEqual(
            detail.title,
            "[Example Initiative] Synthetic challenge registration",
        )
        self.assertEqual(detail.date, date(2031, 2, 9))
        self.assertEqual(detail.author, "Example School")
        self.assertTrue(detail.has_attachment)
        self.assertEqual(len(detail.attachments or []), 2)
        self.assertEqual((detail.attachments or [])[0].file_format, "pdf")
        self.assertEqual((detail.attachments or [])[1].file_format, "xlsx")
        self.assertIn("synthetic challenge", detail.description)


if __name__ == "__main__":
    unittest.main()
