import unittest
from datetime import date
from unittest.mock import AsyncMock, patch

from crawl_skku import cache as skku_cache
from crawl_skku.calendar.models import UpstreamCalendarPayload
from crawl_skku.calendar.root import constants
from crawl_skku.calendar.root.service import RootCalendarService

MONTH_PAYLOAD = UpstreamCalendarPayload.model_validate(
    {
        "data": [
            {
                "articleNo": 132096,
                "title": "Synthetic month event",
                "etcDate1": "2031-02-28",
                "etcDate2": "2031-03-10",
                "categoryId": 17,
                "start": "2031-02-28",
                "end": "2031-03-11",
                "color": "#2e4b82",
                "index": "0",
            },
        ],
        "auth": {"authKey": "23"},
        "success": True,
        "colorMap": {"17": "#2e4b82"},
    }
)

DAY_PAYLOAD = UpstreamCalendarPayload.model_validate(
    {
        "data": [
            {
                "articleNo": 132093,
                "title": "Synthetic day event",
                "etcDate1": "2031-01-24",
                "etcDate2": "2031-02-19",
                "categoryId": 17,
                "url": "?mode=view&articleNo=132093&source=synthetic",
            },
        ],
        "success": True,
        "dayName": "목",
    }
)


class SkkuCalendarRootServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_month_uses_cache_namespace_and_month_key(self) -> None:
        fetch_payload = AsyncMock(return_value=MONTH_PAYLOAD)

        with (
            patch(
                "crawl_skku.calendar.root.service.calendar_service.fetch_calendar_payload",
                fetch_payload,
            ),
            patch(
                "crawl_skku.calendar.root.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            month = await RootCalendarService().get_month(year=2031, month=3)

        fetch_payload.assert_awaited_once_with(
            constants.MONTH_DATA_URL,
            params={"boardNo": constants.BOARD_NO, "date": "2031-03-01"},
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["namespace"], constants.BOARD_NAME
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"],
            skku_cache.CacheResource.CALENDAR_MONTH,
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["key"], {"year": 2031, "month": 3}
        )
        self.assertEqual(month.year, 2031)
        self.assertEqual(month.month, 3)
        self.assertEqual(month.events[0].key.article_no, 132096)

    async def test_get_day_uses_cache_namespace_and_day_key(self) -> None:
        fetch_payload = AsyncMock(return_value=DAY_PAYLOAD)

        with (
            patch(
                "crawl_skku.calendar.root.service.calendar_service.fetch_calendar_payload",
                fetch_payload,
            ),
            patch(
                "crawl_skku.calendar.root.service.skku_cache.get_or_load"
            ) as get_or_load,
        ):

            async def passthrough(**kwargs):
                return await kwargs["loader"]()

            get_or_load.side_effect = passthrough
            day = await RootCalendarService().get_day(date(2031, 2, 4))

        fetch_payload.assert_awaited_once_with(
            constants.DAY_DATA_URL,
            params={
                "boardNo": constants.BOARD_NO,
                "date": "2031-02-04",
                "type": constants.DAY_TYPE,
            },
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["namespace"], constants.BOARD_NAME
        )
        self.assertEqual(
            get_or_load.call_args.kwargs["resource"],
            skku_cache.CacheResource.CALENDAR_DAY,
        )
        self.assertEqual(get_or_load.call_args.kwargs["key"], {"date": "2031-02-04"})
        self.assertEqual(day.date, date(2031, 2, 4))
        self.assertEqual(day.day_name, "목")
        self.assertEqual(day.events[0].key.article_no, 132093)


if __name__ == "__main__":
    unittest.main()
