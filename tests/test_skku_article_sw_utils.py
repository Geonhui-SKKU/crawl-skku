import unittest
from datetime import date
from urllib.parse import urljoin

from crawl_skku.article.sw import constants, utils

LIST_HTML = """
<ul class="board-list-wrap">
  <li>
    <dl>
      <dt class="board-list-content-title">
        <span class="c-board-list-category">[일반]</span>
        <a href="?mode=view&amp;articleNo=218961&amp;article.offset=0&amp;articleLimit=10">
          Synthetic review process notice
        </a>
      </dt>
      <dd class="board-list-content-info">
        <ul>
          <li>No.3001</li>
          <li>Example College</li>
          <li>2031-02-11</li>
          <li>조회수<span>713</span></li>
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
    <h4><span>[일반]</span>Synthetic review process notice</h4>
    <ul class="board-etc-wrap">
      <li>Example College</li>
      <li>조회수<span>713</span></li>
      <li>2031-02-11</li>
    </ul>
  </div>
  <ul class="board-view-file-wrap">
    <li>
      <a class="file-down-btn pdf" href="?mode=download&amp;articleNo=218961&amp;attachNo=193891">
        synthetic-review-guide.pdf
      </a>
    </li>
  </ul>
  <div class="board-view-content-wrap board-view-txt">
    <div class="fr-view">
      <p>* Synthetic review guidance</p>
      <p>This is a synthetic body excerpt.</p>
    </div>
  </div>
</div>
"""


DETAIL_WITH_INLINE_IMAGE_HTML = """
<div class="board-view-box">
  <div class="board-view-title-wrap">
    <h4><span>[일반]</span>인라인 이미지 안내</h4>
    <ul class="board-etc-wrap">
      <li>Example College</li>
      <li>조회수<span>713</span></li>
      <li>2031-02-11</li>
    </ul>
  </div>
  <ul class="board-view-file-wrap"></ul>
  <div class="board-view-content-wrap board-view-txt">
    <div class="fr-view">
      <p>Synthetic body text.</p>
      <img title="sample-poster" src="/_attach/image/2031/02/sample-poster.png" />
    </div>
  </div>
</div>
"""


class SkkuSwParserTests(unittest.TestCase):
    def test_parse_post_list(self) -> None:
        items = utils.parse_post_list(LIST_HTML)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].key.type, "skku_article")
        self.assertEqual(items[0].key.article_no, 218961)
        self.assertEqual(items[0].category, "일반")
        self.assertEqual(items[0].date, date(2031, 2, 11))
        self.assertEqual(items[0].author, "Example College")
        self.assertTrue(items[0].has_attachment)

    def test_parse_post_detail(self) -> None:
        detail = utils.parse_post_detail(DETAIL_HTML, article_no=218961)

        self.assertEqual(detail.key.type, "skku_article")
        self.assertEqual(detail.key.article_no, 218961)
        self.assertEqual(detail.category, "일반")
        self.assertEqual(detail.title, "Synthetic review process notice")
        self.assertEqual(detail.date, date(2031, 2, 11))
        self.assertEqual(detail.author, "Example College")
        self.assertTrue(detail.has_attachment)
        self.assertEqual(len(detail.attachments or []), 1)
        self.assertEqual((detail.attachments or [])[0].file_format, "pdf")
        self.assertIn("Synthetic review guidance", detail.description)

    def test_parse_post_detail_with_inline_image_attachment(self) -> None:
        detail = utils.parse_post_detail(
            DETAIL_WITH_INLINE_IMAGE_HTML,
            article_no=218962,
        )

        self.assertTrue(detail.has_attachment)
        self.assertEqual(len(detail.attachments or []), 1)
        attachment = (detail.attachments or [])[0]
        self.assertEqual(attachment.name, "sample-poster")
        self.assertEqual(attachment.file_format, "png")
        self.assertEqual(
            attachment.url,
            urljoin(
                constants.BOARD_BASE_URL, "/_attach/image/2031/02/sample-poster.png"
            ),
        )
        self.assertEqual(detail.description, "Synthetic body text.")


if __name__ == "__main__":
    unittest.main()
