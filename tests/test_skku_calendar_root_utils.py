import unittest
from datetime import date

from pydantic import ValidationError

from crawl_skku.calendar import service as calendar_service
from crawl_skku.calendar.models import UpstreamCalendarPayload
from crawl_skku.calendar.root import utils
from crawl_skku.exceptions import SkkuParseError

MONTH_UPSTREAM = {
    "data": [
        {
            "articleNo": 137099,
            "title": "Synthetic event alpha",
            "etcDate1": "2031-01-13",
            "etcDate2": "2031-02-03",
            "categoryId": 23,
            "campusCd": "",
            "buildNo": "",
            "start": "2031-01-13",
            "end": "2031-02-04",
            "color": "#000000",
            "index": "6",
        },
        {
            "articleNo": 132093,
            "title": "Synthetic event beta",
            "etcDate1": "2031-01-24",
            "etcDate2": "2031-02-19",
            "categoryId": 17,
            "start": "2031-01-24",
            "end": "2031-02-20",
            "color": "#2e4b82",
            "index": "0",
        },
        {
            "articleNo": 132099,
            "title": "Synthetic event gamma",
            "etcDate1": "2031-02-19",
            "etcDate2": "2031-02-19",
            "start": "2031-02-19",
            "end": "2031-02-20",
        },
    ],
    "todayName": "일",
    "auth": {"authKey": "23"},
    "success": True,
    "today": "2031-02-14",
    "todayData": [],
    "type": "",
    "colorMap": {"17": "#2e4b82", "23": "#000000"},
}

DAY_UPSTREAM = {
    "data": [
        {
            "articleNo": 132093,
            "title": "Synthetic event beta",
            "etcDate1": "2031-01-24",
            "etcDate2": "2031-02-19",
            "categoryId": 17,
            "url": "?mode=view&articleNo=132093&source=synthetic",
        },
        {
            "articleNo": 132094,
            "title": "Synthetic event delta",
            "etcDate1": "2031-01-26",
            "etcDate2": "2031-02-05",
            "categoryId": 17,
            "url": "?mode=view&articleNo=132094&source=synthetic",
        },
    ],
    "todayName": "일",
    "dayName": "목",
    "auth": {"authKey": "23"},
    "success": True,
}


class SkkuCalendarRootParserTests(unittest.IsolatedAsyncioTestCase):
    def test_parse_month_payload_normalizes_upstream_fields(self) -> None:
        payload = UpstreamCalendarPayload.model_validate(MONTH_UPSTREAM)

        month = utils.parse_month_payload(payload, year=2031, month=2)

        self.assertEqual(month.year, 2031)
        self.assertEqual(month.month, 2)
        self.assertEqual(len(month.events), 3)
        self.assertEqual(month.events[0].key.type, "skku_calendar_event")
        self.assertEqual(month.events[0].key.article_no, 137099)
        self.assertEqual(month.events[0].start_date, date(2031, 1, 13))
        self.assertEqual(month.events[0].end_date, date(2031, 2, 3))
        self.assertEqual(month.events[0].category_id, 23)
        self.assertIsNone(month.events[2].category_id)

    def test_parse_day_payload_includes_day_name(self) -> None:
        payload = UpstreamCalendarPayload.model_validate(DAY_UPSTREAM)

        day = utils.parse_day_payload(payload, day=date(2031, 2, 4))

        self.assertEqual(day.date, date(2031, 2, 4))
        self.assertEqual(day.day_name, "목")
        self.assertEqual(len(day.events), 2)
        self.assertEqual(day.events[1].key.article_no, 132094)
        self.assertEqual(day.events[1].end_date, date(2031, 2, 5))

    def test_upstream_payload_rejects_missing_required_event_fields(self) -> None:
        invalid = {
            "data": [{"articleNo": 1, "title": "Missing dates"}],
            "success": True,
        }

        with self.assertRaises(ValidationError):
            UpstreamCalendarPayload.model_validate(invalid)

    async def test_fetch_calendar_payload_rejects_invalid_json(self) -> None:
        async def fake_fetch_html(url, params=None):
            return "not-json"

        original_fetch_html = calendar_service.skku_service.fetch_html
        calendar_service.skku_service.fetch_html = fake_fetch_html
        try:
            with self.assertRaises(SkkuParseError):
                await calendar_service.fetch_calendar_payload(
                    "https://example.com", params={}
                )
        finally:
            calendar_service.skku_service.fetch_html = original_fetch_html


if __name__ == "__main__":
    unittest.main()
