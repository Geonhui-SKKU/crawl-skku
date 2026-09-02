import unittest
from datetime import date
from urllib.parse import urljoin

from crawl_skku.article.cse import constants, utils

LIST_HTML = """
<ul class="board-list-wrap">
  <li>
    <dl>
      <dt class="board-list-content-title board-list-content-top">
        <span class="c-board-list-category">[학사]</span>
        <a href="?mode=view&amp;articleNo=218999&amp;article.offset=0&amp;articleLimit=10">
          [Academic] Synthetic evaluation notice
        </a>
      </dt>
      <dd class="board-list-content-info">
        <ul>
          <li>공지</li>
          <li>Example Department</li>
          <li>2031-02-12</li>
          <li>조회수<span>1231</span></li>
        </ul>
      </dd>
    </dl>
    <div class="board-list-etc-wrap"><ul></ul></div>
  </li>
  <li>
    <dl>
      <dt class="board-list-content-title">
        <span class="c-board-list-category">[채용/모집]</span>
        <a href="?mode=view&amp;articleNo=219187&amp;article.offset=0&amp;articleLimit=10">
          Synthetic training enrollment
        </a>
      </dt>
      <dd class="board-list-content-info">
        <ul>
          <li>No.1169</li>
          <li>Example Department</li>
          <li>2031-02-16</li>
          <li>조회수<span>77</span></li>
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
    <h4><span>[채용/모집]</span>Synthetic training enrollment</h4>
    <ul class="board-etc-wrap">
      <li>Example Department</li>
      <li>조회수<span>77</span></li>
      <li>2031-02-16</li>
    </ul>
  </div>
  <div class="board-view-content-wrap board-view-txt">
    <div class="fr-view">
      <p>This is a synthetic training description.</p>
      <img src="/_res/editor_image/2031/02/sample-training.jpg" />
    </div>
  </div>
</div>
"""


class SkkuCseParserTests(unittest.TestCase):
    def test_parse_post_list(self) -> None:
        items = utils.parse_post_list(LIST_HTML)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].key.type, "skku_article")
        self.assertEqual(items[0].key.article_no, 218999)
        self.assertEqual(items[0].category, "학사")
        self.assertEqual(items[0].date, date(2031, 2, 12))
        self.assertEqual(items[0].author, "Example Department")
        self.assertFalse(items[0].has_attachment)
        self.assertEqual(items[1].key.article_no, 219187)
        self.assertEqual(items[1].category, "채용/모집")
        self.assertTrue(items[1].has_attachment)

    def test_parse_post_detail_with_inline_image_attachment(self) -> None:
        detail = utils.parse_post_detail(DETAIL_HTML, article_no=219187)

        self.assertEqual(detail.key.type, "skku_article")
        self.assertEqual(detail.key.article_no, 219187)
        self.assertEqual(detail.category, "채용/모집")
        self.assertEqual(detail.title, "Synthetic training enrollment")
        self.assertEqual(detail.date, date(2031, 2, 16))
        self.assertEqual(detail.author, "Example Department")
        self.assertTrue(detail.has_attachment)
        self.assertEqual(len(detail.attachments or []), 1)
        attachment = (detail.attachments or [])[0]
        self.assertEqual(attachment.name, "sample-training.jpg")
        self.assertEqual(attachment.file_format, "jpg")
        self.assertEqual(
            attachment.url,
            urljoin(
                constants.BOARD_BASE_URL,
                "/_res/editor_image/2031/02/sample-training.jpg",
            ),
        )
        self.assertIn("synthetic training", detail.description)


if __name__ == "__main__":
    unittest.main()
