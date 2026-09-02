from datetime import date

from crawl_skku.calendar import utils as calendar_utils
from crawl_skku.calendar.models import UpstreamCalendarPayload
from crawl_skku.calendar.schemas import SkkuCalendarDay, SkkuCalendarMonth


def parse_month_payload(
    payload: UpstreamCalendarPayload,
    *,
    year: int,
    month: int,
) -> SkkuCalendarMonth:
    return SkkuCalendarMonth(
        year=year,
        month=month,
        events=[
            calendar_utils.normalize_calendar_event(event) for event in payload.data
        ],
    )


def parse_day_payload(
    payload: UpstreamCalendarPayload, *, day: date
) -> SkkuCalendarDay:
    return SkkuCalendarDay(
        date=day,
        day_name=payload.day_name,
        events=[
            calendar_utils.normalize_calendar_event(event) for event in payload.data
        ],
    )
