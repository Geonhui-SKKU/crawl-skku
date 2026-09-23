import unittest

from crawl_skku.api import app


class SkkuNewBoardRouteTests(unittest.TestCase):
    def test_openapi_contains_new_board_routes(self) -> None:
        paths = app.openapi()["paths"]

        self.assertIn("/skku/article/sw/posts", paths)
        self.assertIn("/skku/article/sw/posts/{article_no}", paths)
        self.assertIn("/skku/article/skb_swuniv/posts", paths)
        self.assertIn("/skku/article/skb_swuniv/posts/{article_no}", paths)
        self.assertIn("/skku/article/cse/posts", paths)
        self.assertIn("/skku/article/cse/posts/{article_no}", paths)
        self.assertIn("/skku/article/sco/posts", paths)
        self.assertIn("/skku/article/sco/posts/{article_no}", paths)
        self.assertIn("/skku/article/enc/posts", paths)
        self.assertIn("/skku/article/enc/posts/{article_no}", paths)
        self.assertIn("/skku/article/ice/posts", paths)
        self.assertIn("/skku/article/ice/posts/{article_no}", paths)

    def test_openapi_article_routes_have_single_source_tag(self) -> None:
        paths = app.openapi()["paths"]

        self.assertEqual(
            paths["/skku/article/sw/posts"]["get"]["tags"],
            ["SKKU SW posts"],
        )
        self.assertEqual(
            paths["/skku/article/skb_swuniv/posts"]["get"]["tags"],
            ["SKKU SKB SWUNIV posts"],
        )
        self.assertEqual(
            paths["/skku/article/cse/posts"]["get"]["tags"],
            ["SKKU CSE posts"],
        )
        self.assertEqual(
            paths["/skku/article/sco/posts"]["get"]["tags"],
            ["SKKU SCO posts"],
        )
        self.assertEqual(
            paths["/skku/article/enc/posts"]["get"]["tags"],
            ["SKKU ENC posts"],
        )
        self.assertEqual(
            paths["/skku/article/ice/posts"]["get"]["tags"],
            ["SKKU ICE posts"],
        )


if __name__ == "__main__":
    unittest.main()
