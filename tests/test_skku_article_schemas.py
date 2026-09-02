import unittest
from datetime import date

from pydantic import ValidationError

from crawl_skku.article.schemas import ArticlePostListItem, SkkuArticlePostListItem


class SkkuSchemaTests(unittest.TestCase):
    def test_shared_post_accepts_arbitrary_key_object(self) -> None:
        item = ArticlePostListItem(
            key={"type": "custom_board", "id": "abc-123"},
            title="Custom post",
            date=date(2031, 2, 14),
            url="https://example.com/posts/abc-123",
        )

        self.assertEqual(
            item.key.model_extra, {"type": "custom_board", "id": "abc-123"}
        )

    def test_skku_article_post_accepts_typed_article_key(self) -> None:
        item = SkkuArticlePostListItem(
            key={"type": "skku_article", "article_no": 137297},
            title="Synthetic post",
            date=date(2031, 2, 14),
            url="https://example.test/posts/137297",
        )

        self.assertEqual(item.key.type, "skku_article")
        self.assertEqual(item.key.article_no, 137297)

    def test_skku_article_post_rejects_missing_type(self) -> None:
        with self.assertRaises(ValidationError):
            SkkuArticlePostListItem(
                key={"article_no": 137297},
                title="Synthetic post",
                date=date(2031, 2, 14),
                url="https://example.test/posts/137297",
            )

    def test_skku_article_post_rejects_wrong_type(self) -> None:
        with self.assertRaises(ValidationError):
            SkkuArticlePostListItem(
                key={"type": "custom_board", "article_no": 137297},
                title="Synthetic post",
                date=date(2031, 2, 14),
                url="https://example.test/posts/137297",
            )

    def test_skku_article_post_rejects_non_numeric_article_no(self) -> None:
        with self.assertRaises(ValidationError):
            SkkuArticlePostListItem(
                key={"type": "skku_article", "article_no": "not-a-number"},
                title="Synthetic post",
                date=date(2031, 2, 14),
                url="https://example.test/posts/137297",
            )


if __name__ == "__main__":
    unittest.main()
