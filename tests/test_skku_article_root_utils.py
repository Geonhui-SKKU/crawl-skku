import unittest
from datetime import date
from urllib.parse import urljoin

from crawl_skku.article.root import constants, utils

LIST_HTML = """
<ul class="board-list-wrap">
  <li>
    <dl class="board-list-content-wrap">
      <dt class="board-list-content-title">
        <span class="c-board-list-category">[채용/모집]</span>
        <a href="?mode=view&amp;articleNo=137555&amp;article.offset=0&amp;articleLimit=10">
          Synthetic workshop registration notice
        </a>
      </dt>
      <dd class="board-list-content-info">
        <ul>
          <li>No.25231</li>
          <li>Sample Office</li>
          <li>2031-02-14</li>
          <li>조회수<span>3764</span></li>
        </ul>
      </dd>
    </dl>
    <div class="board-list-etc-wrap"><ul></ul></div>
  </li>
  <li>
    <dl class="board-list-content-wrap">
      <dt class="board-list-content-title">
        <a href="?mode=view&amp;articleNo=137297">
          Synthetic project participant call
        </a>
      </dt>
      <dd class="board-list-content-info">
        <ul>
          <li>No.82</li>
          <li>Example Center</li>
          <li>2031.02.13</li>
          <li>조회수<span>16159</span></li>
        </ul>
      </dd>
    </dl>
    <div class="board-list-etc-wrap">
      <ul>
        <li class="c-board-file-icon board-list-file">
          <span class="hide">첨부파일</span>
        </li>
      </ul>
    </div>
  </li>
</ul>
"""


DETAIL_HTML = """
<table class="board_view">
  <thead>
    <tr>
      <th>
        <span class="category">[학사]</span>
        <em class="ellipsis">Synthetic term program notice</em>
        <span class="date">최종 수정일 : 2031.02.08</span>
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <div class="boardView_txtWrap">
          <div class="flL">
            <ul class="boardView_txtList">
              <li class="noline">Example Team</li>
            </ul>
          </div>
          <div class="flR">
            <ul class="boardView_txtList">
              <li>
                <a class="file" href="#">첨부파일 <span>( 2 )</span></a>
                <div class="file_downWrap">
                  <ul class="filedown_list">
                    <li>
                      <a class="ellipsis" href="?mode=download&amp;articleNo=137564&amp;attachNo=115063">
                        synthetic-program-guide.pdf
                      </a>
                    </li>
                    <li>
                      <a class="ellipsis" href="?mode=download&amp;articleNo=137564&amp;attachNo=115064">
                        synthetic-program-faq.pdf
                      </a>
                    </li>
                  </ul>
                </div>
              </li>
            </ul>
          </div>
        </div>
        <dl class="board-write-box board-write-box-v03">
          <dt class="hide replyNone">게시글 내용</dt>
          <dd>
            <pre class="pre">This is a synthetic program announcement.

1. Example schedule</pre>
          </dd>
        </dl>
      </td>
    </tr>
  </tbody>
</table>
"""


DETAIL_WITHOUT_OPTIONAL_HTML = """
<table class="board_view">
  <thead>
    <tr>
      <th>
        <em class="ellipsis">Synthetic post without optional fields</em>
        <span class="date">최종 수정일 : 2031-02-07</span>
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <div class="boardView_txtWrap">
          <div class="flL">
            <ul class="boardView_txtList"><li>Example Admin</li></ul>
          </div>
        </div>
        <dl class="board-write-box"><dd>Synthetic body text.</dd></dl>
      </td>
    </tr>
  </tbody>
</table>
"""


DETAIL_WITH_INLINE_IMAGE_HTML = """
<table class="board_view">
  <thead>
    <tr>
      <th>
        <span class="category">[행사/세미나]</span>
        <em class="ellipsis">Synthetic post with inline images</em>
        <span class="date">최종 수정일 : 2031.02.12</span>
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <div class="boardView_txtWrap">
          <div class="flL">
            <ul class="boardView_txtList"><li>Example Author</li></ul>
          </div>
          <div class="flR">
            <ul class="boardView_txtList">
              <li>
                <a class="file" href="#">첨부파일 <span>( 0 )</span></a>
                <div class="file_downWrap">
                  <ul class="filedown_list"></ul>
                </div>
              </li>
            </ul>
          </div>
        </div>
        <dl class="board-write-box board-write-box-v03">
          <dt class="hide replyNone">게시글 내용</dt>
          <dd>
            <pre class="pre">Synthetic body text.</pre>
            <img alt="sample-image" src="/_attach/image/2031/02/synthetic-image.jpg" />
            <img alt="sample-poster.png" src="/_attach/image/2031/02/sample-poster.png" />
          </dd>
        </dl>
      </td>
    </tr>
  </tbody>
</table>
"""


class SkkuRootArticleParserTests(unittest.TestCase):
    def test_parse_post_list(self) -> None:
        items = utils.parse_post_list(LIST_HTML)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].key.type, "skku_article")
        self.assertEqual(items[0].key.article_no, 137555)
        self.assertEqual(items[0].category, "채용/모집")
        self.assertEqual(items[0].title, "Synthetic workshop registration notice")
        self.assertEqual(items[0].date, date(2031, 2, 14))
        self.assertEqual(items[0].author, "Sample Office")
        self.assertFalse(items[0].has_attachment)
        self.assertEqual(items[1].category, None)
        self.assertEqual(items[1].key.type, "skku_article")
        self.assertEqual(items[1].key.article_no, 137297)
        self.assertEqual(items[1].date, date(2031, 2, 13))
        self.assertTrue(items[1].has_attachment)

    def test_parse_post_detail_with_attachments(self) -> None:
        detail = utils.parse_post_detail(DETAIL_HTML, article_no=137564)

        self.assertEqual(detail.key.type, "skku_article")
        self.assertEqual(detail.key.article_no, 137564)
        self.assertEqual(detail.category, "학사")
        self.assertEqual(detail.title, "Synthetic term program notice")
        self.assertEqual(detail.date, date(2031, 2, 8))
        self.assertEqual(detail.author, "Example Team")
        self.assertTrue(detail.has_attachment)
        self.assertIsNotNone(detail.attachments)
        self.assertEqual(len(detail.attachments or []), 2)
        self.assertEqual((detail.attachments or [])[0].file_format, "pdf")
        self.assertIn("This is a synthetic program announcement.", detail.description)
        self.assertNotIn("synthetic-program-faq.pdf", detail.description)

    def test_parse_post_detail_without_optional_fields(self) -> None:
        detail = utils.parse_post_detail(
            DETAIL_WITHOUT_OPTIONAL_HTML,
            article_no=137565,
        )

        self.assertIsNone(detail.category)
        self.assertIsNone(detail.attachments)
        self.assertFalse(detail.has_attachment)
        self.assertEqual(detail.description, "Synthetic body text.")

    def test_parse_post_detail_with_inline_image_attachment(self) -> None:
        detail = utils.parse_post_detail(
            DETAIL_WITH_INLINE_IMAGE_HTML,
            article_no=137696,
        )

        self.assertTrue(detail.has_attachment)
        self.assertEqual(len(detail.attachments or []), 2)

        attachment1 = (detail.attachments or [])[0]
        self.assertEqual(attachment1.name, "sample-image.jpg")
        self.assertEqual(attachment1.file_format, "jpg")
        self.assertEqual(
            attachment1.url,
            urljoin(
                constants.BOARD_BASE_URL, "/_attach/image/2031/02/synthetic-image.jpg"
            ),
        )

        attachment2 = (detail.attachments or [])[1]
        self.assertEqual(attachment2.name, "sample-poster.png")
        self.assertEqual(attachment2.file_format, "png")
        self.assertEqual(
            attachment2.url,
            urljoin(
                constants.BOARD_BASE_URL, "/_attach/image/2031/02/sample-poster.png"
            ),
        )
        self.assertEqual(detail.description, "Synthetic body text.")


if __name__ == "__main__":
    unittest.main()
