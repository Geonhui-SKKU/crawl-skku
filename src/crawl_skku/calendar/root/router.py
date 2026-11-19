from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from crawl_skku.calendar.root.dependencies import RootCalendarServiceDep
from crawl_skku.calendar.schemas import SkkuCalendarDay, SkkuCalendarMonth
from crawl_skku.exceptions import SkkuCrawlerError

router = APIRouter(tags=["성균관대학교 학사일정"])


@router.get(
    "/month",
    summary="월별 학사일정 조회",
)
async def get_month(
    service: RootCalendarServiceDep,
    year: Annotated[int, Query(ge=1)],
    month: Annotated[int, Query(ge=1, le=12)],
) -> SkkuCalendarMonth:
    try:
        return await service.get_month(year=year, month=month)
    except SkkuCrawlerError as exc:
        raise _bad_gateway(exc) from exc


@router.get(
    "/days/{date}",
    summary="일별 학사일정 조회",
)
async def get_day(
    service: RootCalendarServiceDep,
    calendar_date: Annotated[date, Path(alias="date")],
) -> SkkuCalendarDay:
    try:
        return await service.get_day(calendar_date)
    except SkkuCrawlerError as exc:
        raise _bad_gateway(exc) from exc


def _bad_gateway(exc: SkkuCrawlerError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(exc) or "Failed to read SKKU calendar upstream data",
    )
