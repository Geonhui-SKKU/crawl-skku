from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class UpstreamCalendarEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    article_no: int = Field(alias="articleNo", ge=1)
    title: str = Field(min_length=1)
    etc_date_1: date = Field(alias="etcDate1")
    etc_date_2: date = Field(alias="etcDate2")
    category_id: int | None = Field(default=None, alias="categoryId")


class UpstreamCalendarPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    data: list[UpstreamCalendarEvent]
    success: bool = True
    day_name: str | None = Field(default=None, alias="dayName")
