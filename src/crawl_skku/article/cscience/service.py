from crawl_skku import cache as skku_cache
from crawl_skku import service as skku_service
from crawl_skku.article.cscience import constants, utils
from crawl_skku.article.cscience.schemas import CscienceArticlePostDetail
from crawl_skku.article.schemas import ArticlePostListItem


class CscienceArticlePostService:
    async def get_posts(
        self,
        offset: int = 0,
        limit: int = constants.DEFAULT_LIMIT,
    ) -> list[ArticlePostListItem]:
        settings = skku_cache.get_cache_settings()
        return await skku_cache.get_or_load(
            namespace=constants.BOARD_NAME,
            resource=skku_cache.CacheResource.POST_LIST,
            key={"offset": offset, "limit": limit},
            ttl_seconds=skku_cache.list_ttl(settings),
            response_type=list[ArticlePostListItem],
            loader=lambda: self._load_posts(offset=offset, limit=limit),
            settings=settings,
        )

    async def get_post(self, board_id: int, item_id: str) -> CscienceArticlePostDetail:
        settings = skku_cache.get_cache_settings()
        return await skku_cache.get_or_load(
            namespace=constants.BOARD_NAME,
            resource=skku_cache.CacheResource.POST_DETAIL,
            key={"board_id": board_id, "item_id": item_id},
            ttl_seconds=skku_cache.detail_ttl(settings),
            response_type=CscienceArticlePostDetail,
            loader=lambda: self._load_post(board_id=board_id, item_id=item_id),
            settings=settings,
        )

    async def _load_posts(
        self,
        offset: int,
        limit: int,
    ) -> list[ArticlePostListItem]:
        html = await skku_service.fetch_html(
            constants.BOARD_BASE_URL,
            params={"article.offset": offset, "articleLimit": limit},
        )
        return utils.parse_post_list(html)[:limit]

    async def _load_post(
        self, board_id: int, item_id: str
    ) -> CscienceArticlePostDetail:
        html = await skku_service.fetch_html(
            constants.BOARD_BASE_URL,
            params={"mode": "view", "viewBoardId": board_id, "itemId": item_id},
        )
        return utils.parse_post_detail(html, board_id=board_id, item_id=item_id)
