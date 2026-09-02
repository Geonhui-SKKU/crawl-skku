from typing import Annotated

from fastapi import Depends

from crawl_skku.calendar.root.service import RootCalendarService


async def get_root_calendar_service() -> RootCalendarService:
    return RootCalendarService()


RootCalendarServiceDep = Annotated[
    RootCalendarService,
    Depends(get_root_calendar_service),
]
