from datetime import date

from crawl_skku.calendar import constants
from crawl_skku.calendar.models import UpstreamCalendarEvent
from crawl_skku.calendar.schemas import SkkuCalendarEvent, SkkuCalendarEventKey


def month_anchor_date(year: int, month: int) -> date:
    return date(year, month, constants.DEFAULT_MONTH_DAY)


def normalize_calendar_event(event: UpstreamCalendarEvent) -> SkkuCalendarEvent:
    return SkkuCalendarEvent(
        key=SkkuCalendarEventKey(
            type="skku_calendar_event",
            article_no=event.article_no,
        ),
        title=event.title,
        start_date=event.etc_date_1,
        end_date=event.etc_date_2,
        category_id=event.category_id,
    )
