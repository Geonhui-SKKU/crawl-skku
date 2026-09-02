from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class SkkuCalendarEventKey(BaseModel):
    type: Literal["skku_calendar_event"]
    article_no: int = Field(ge=1)


class SkkuCalendarEvent(BaseModel):
    key: SkkuCalendarEventKey
    title: str = Field(min_length=1)
    start_date: date
    end_date: date
    category_id: int | None = None


class SkkuCalendarMonth(BaseModel):
    year: int = Field(ge=1)
    month: int = Field(ge=1, le=12)
    events: list[SkkuCalendarEvent]


class SkkuCalendarDay(BaseModel):
    date: date
    day_name: str | None = None
    events: list[SkkuCalendarEvent]
