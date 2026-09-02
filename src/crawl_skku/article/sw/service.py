from crawl_skku import cache as skku_cache
from crawl_skku import service as skku_service
from crawl_skku.article.schemas import SkkuArticlePostDetail, SkkuArticlePostListItem
from crawl_skku.article.sw import constants, utils


class SwArticlePostService:
    async def get_posts(
        self,
        offset: int = 0,
        limit: int = constants.DEFAULT_LIMIT,
    ) -> list[SkkuArticlePostListItem]:
        settings = skku_cache.get_cache_settings()
        return await skku_cache.get_or_load(
            namespace=constants.BOARD_NAME,
            resource=skku_cache.CacheResource.POST_LIST,
            key={"offset": offset, "limit": limit},
            ttl_seconds=skku_cache.list_ttl(settings),
            response_type=list[SkkuArticlePostListItem],
            loader=lambda: self._load_posts(offset=offset, limit=limit),
            settings=settings,
        )

    async def get_post(self, article_no: int) -> SkkuArticlePostDetail:
        settings = skku_cache.get_cache_settings()
        return await skku_cache.get_or_load(
            namespace=constants.BOARD_NAME,
            resource=skku_cache.CacheResource.POST_DETAIL,
            key={"article_no": article_no},
            ttl_seconds=skku_cache.detail_ttl(settings),
            response_type=SkkuArticlePostDetail,
            loader=lambda: self._load_post(article_no=article_no),
            settings=settings,
        )

    async def _load_posts(
        self,
        offset: int,
        limit: int,
    ) -> list[SkkuArticlePostListItem]:
        html = await skku_service.fetch_html(
            constants.BOARD_BASE_URL,
            params={"article.offset": offset, "articleLimit": limit},
        )
        return utils.parse_post_list(html)[:limit]

    async def _load_post(self, article_no: int) -> SkkuArticlePostDetail:
        html = await skku_service.fetch_html(
            constants.BOARD_BASE_URL,
            params={"mode": "view", "articleNo": article_no},
        )
        return utils.parse_post_detail(html, article_no=article_no)
