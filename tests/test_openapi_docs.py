import unittest

from httpx import ASGITransport, AsyncClient

from crawl_skku.api import app
from crawl_skku.article.metadata import SOURCE_NAMES


class OpenApiDocsTests(unittest.IsolatedAsyncioTestCase):
    async def test_swagger_uses_the_localized_openapi_schema(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            docs = await client.get("/docs")
            schema = await client.get("/openapi.json")

        self.assertEqual(docs.status_code, 200)
        self.assertIn("/openapi.json", docs.text)
        self.assertEqual(schema.status_code, 200)
        paths = schema.json()["paths"]
        self.assertEqual(
            paths["/skku/article/comedu/posts"]["get"]["tags"],
            ["성균관대학교 컴퓨터교육과 공지사항"],
        )
        self.assertEqual(
            paths["/skku/article/gbme/posts"]["get"]["tags"],
            ["성균관대학교 글로벌바이오메디컬공학과 공지사항"],
        )

    def test_each_article_source_has_one_distinct_tag_for_list_and_detail(self) -> None:
        paths = app.openapi()["paths"]
        by_source: dict[str, str] = {}
        for path, operations in paths.items():
            if not path.startswith("/skku/article/"):
                continue
            source = path.split("/")[3]
            operation = operations["get"]
            with self.subTest(path=path):
                self.assertEqual(len(operation["tags"]), 1)
                (tag,) = operation["tags"]
                self.assertTrue(tag.startswith("성균관대학교 "))
                self.assertTrue(tag.endswith(" 공지사항"))
                self.assertEqual(tag, by_source.setdefault(source, tag))
                self.assertEqual(
                    operation["summary"],
                    "공지사항 목록 조회"
                    if path.endswith("/posts")
                    else "공지사항 상세 조회",
                )
        self.assertCountEqual(by_source, SOURCE_NAMES)
        self.assertEqual(len(set(by_source.values())), len(by_source))
