from datetime import date

from crawl_skku import cache as skku_cache
from crawl_skku.calendar import service as calendar_service
from crawl_skku.calendar import utils as calendar_utils
from crawl_skku.calendar.root import constants, utils
from crawl_skku.calendar.schemas import SkkuCalendarDay, SkkuCalendarMonth


class RootCalendarService:
    async def get_month(self, year: int, month: int) -> SkkuCalendarMonth:
        settings = skku_cache.get_cache_settings()
        return await skku_cache.get_or_load(
            namespace=constants.BOARD_NAME,
            resource=skku_cache.CacheResource.CALENDAR_MONTH,
            key={"year": year, "month": month},
            ttl_seconds=skku_cache.list_ttl(settings),
            response_type=SkkuCalendarMonth,
            loader=lambda: self._load_month(year=year, month=month),
            settings=settings,
        )

    async def get_day(self, day: date) -> SkkuCalendarDay:
        settings = skku_cache.get_cache_settings()
        return await skku_cache.get_or_load(
            namespace=constants.BOARD_NAME,
            resource=skku_cache.CacheResource.CALENDAR_DAY,
            key={"date": day.isoformat()},
            ttl_seconds=skku_cache.list_ttl(settings),
            response_type=SkkuCalendarDay,
            loader=lambda: self._load_day(day),
            settings=settings,
        )

    async def _load_month(self, year: int, month: int) -> SkkuCalendarMonth:
        anchor_date = calendar_utils.month_anchor_date(year, month)
        payload = await calendar_service.fetch_calendar_payload(
            constants.MONTH_DATA_URL,
            params={
                "boardNo": constants.BOARD_NO,
                "date": anchor_date.isoformat(),
            },
        )
        return utils.parse_month_payload(payload, year=year, month=month)

    async def _load_day(self, day: date) -> SkkuCalendarDay:
        payload = await calendar_service.fetch_calendar_payload(
            constants.DAY_DATA_URL,
            params={
                "boardNo": constants.BOARD_NO,
                "date": day.isoformat(),
                "type": constants.DAY_TYPE,
            },
        )
        return utils.parse_day_payload(payload, day=day)
