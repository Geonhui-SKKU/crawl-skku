from crawl_skku import cache as skku_cache
from crawl_skku import service as skku_service
from crawl_skku.article.enc import constants, utils
from crawl_skku.article.schemas import SkkuArticlePostDetail, SkkuArticlePostListItem


class EncArticlePostService:
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

    async def get_item_post(
        self, article_no: int, board_id: int, item_id: str
    ) -> SkkuArticlePostDetail:
        settings = skku_cache.get_cache_settings()
        return await skku_cache.get_or_load(
            namespace=constants.BOARD_NAME,
            resource=skku_cache.CacheResource.POST_DETAIL,
            key={"article_no": article_no, "board_id": board_id, "item_id": item_id},
            ttl_seconds=skku_cache.detail_ttl(settings),
            response_type=SkkuArticlePostDetail,
            loader=lambda: self._load_item_post(article_no, board_id, item_id),
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

    async def _load_item_post(
        self, article_no: int, board_id: int, item_id: str
    ) -> SkkuArticlePostDetail:
        html = await skku_service.fetch_html(
            constants.BOARD_BASE_URL,
            params={"mode": "view", "viewBoardId": board_id, "itemId": item_id},
        )
        return utils.parse_post_detail(html, article_no, board_id, item_id)
