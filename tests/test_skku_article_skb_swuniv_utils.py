import unittest
from datetime import date
from urllib.parse import urljoin

from crawl_skku.article.skb_swuniv import constants, utils

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


class SkkuSkbSwunivParserTests(unittest.TestCase):
    def test_parse_post_list(self) -> None:
        items = utils.parse_post_list(LIST_HTML)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].key.type, "skku_article")
        self.assertEqual(items[0].key.article_no, 219037)
        self.assertIsNone(items[0].category)
        self.assertEqual(items[0].date, date(2031, 2, 12))
        self.assertEqual(items[0].author, "Example Program Office")
        self.assertTrue(items[0].has_attachment)

    def test_parse_post_detail(self) -> None:
        detail = utils.parse_post_detail(DETAIL_HTML, article_no=219037)

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
        self.assertIn("synthetic mentor", detail.description)

    def test_parse_post_detail_with_inline_image_attachment(self) -> None:
        detail = utils.parse_post_detail(
            DETAIL_WITH_INLINE_IMAGE_HTML,
            article_no=219038,
        )

        self.assertTrue(detail.has_attachment)
        self.assertEqual(len(detail.attachments or []), 1)
        attachment = (detail.attachments or [])[0]
        self.assertEqual(attachment.name, "sample-poster.jpg")
        self.assertEqual(attachment.file_format, "jpg")
        self.assertEqual(
            attachment.url,
            urljoin(
                constants.BOARD_BASE_URL, "/_attach/image/2031/02/sample-poster.jpg"
            ),
        )
        self.assertEqual(detail.description, "Synthetic body text.")


if __name__ == "__main__":
    unittest.main()
