from abc import abstractmethod

from crawl_skku.article.board_service import CachedArticleBoard
from crawl_skku.article.schemas import SkkuArticlePostListItem


class PagedArticleBoard(CachedArticleBoard[SkkuArticlePostListItem]):
    """Translate a fixed-size upstream page into an offset-based API window."""

    def __init__(
        self, source: str, url: str, page_size: int, *, repeated_pins: bool = False
    ) -> None:
        super().__init__(source, url, list[SkkuArticlePostListItem])
        self._page_size = page_size
        self._repeated_pins = repeated_pins

    @abstractmethod
    async def _load_page(
        self, page: int
    ) -> tuple[list[SkkuArticlePostListItem], list[SkkuArticlePostListItem]]:
        """Return (repeated pinned posts, regular posts on this page)."""

    async def _load_posts(
        self, offset: int, limit: int
    ) -> list[SkkuArticlePostListItem]:
        result: list[SkkuArticlePostListItem] = []
        first_page: list[SkkuArticlePostListItem] | None = None
        if self._repeated_pins:
            pinned, first_page = await self._load_page(1)
            result = pinned[offset : offset + limit]
            offset = max(0, offset - len(pinned))
        page_index, start = divmod(offset, self._page_size)
        while len(result) < limit:
            if page_index == 0 and first_page is not None:
                regular = first_page
            else:
                _, regular = await self._load_page(page_index + 1)
            result.extend(regular[start : start + limit - len(result)])
            if len(regular) < self._page_size:
                break
            page_index += 1
            start = 0
        return result
