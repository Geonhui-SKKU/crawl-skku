import unittest
from datetime import date

from pydantic import ValidationError

from crawl_skku.calendar.schemas import (
    SkkuCalendarDay,
    SkkuCalendarEvent,
    SkkuCalendarMonth,
)


class SkkuCalendarSchemaTests(unittest.TestCase):
    def test_calendar_event_accepts_typed_key(self) -> None:
        event = SkkuCalendarEvent(
            key={"type": "skku_calendar_event", "article_no": 132093},
            title="Synthetic calendar event",
            start_date=date(2031, 1, 24),
            end_date=date(2031, 2, 19),
            category_id=17,
        )

        self.assertEqual(event.key.type, "skku_calendar_event")
        self.assertEqual(event.key.article_no, 132093)

    def test_calendar_event_rejects_wrong_key_type(self) -> None:
        with self.assertRaises(ValidationError):
            SkkuCalendarEvent(
                key={"type": "skku_article", "article_no": 132093},
                title="Calendar event",
                start_date=date(2031, 1, 24),
                end_date=date(2031, 2, 19),
            )

    def test_month_and_day_serialize_dates(self) -> None:
        event = SkkuCalendarEvent(
            key={"type": "skku_calendar_event", "article_no": 132093},
            title="Calendar event",
            start_date=date(2031, 1, 24),
            end_date=date(2031, 2, 19),
        )

        month = SkkuCalendarMonth(year=2031, month=2, events=[event])
        day = SkkuCalendarDay(date=date(2031, 2, 4), day_name="목", events=[event])

        self.assertEqual(
            month.model_dump(mode="json")["events"][0]["start_date"], "2031-01-24"
        )
        self.assertEqual(day.model_dump(mode="json")["date"], "2031-02-04")


if __name__ == "__main__":
    unittest.main()
