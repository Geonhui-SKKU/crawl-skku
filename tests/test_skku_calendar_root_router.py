import unittest
from datetime import date

from httpx import ASGITransport, AsyncClient

from crawl_skku.api import app
from crawl_skku.calendar.root.dependencies import get_root_calendar_service
from crawl_skku.calendar.schemas import (
    SkkuCalendarDay,
    SkkuCalendarEvent,
    SkkuCalendarMonth,
)
from crawl_skku.exceptions import SkkuFetchError


class FakeRootCalendarService:
    def __init__(self) -> None:
        self.month_args: tuple[int, int] | None = None
        self.day_arg: date | None = None

    async def get_month(self, year: int, month: int) -> SkkuCalendarMonth:
        self.month_args = (year, month)
        return SkkuCalendarMonth(
            year=year,
            month=month,
            events=[
                SkkuCalendarEvent(
                    key={"type": "skku_calendar_event", "article_no": 132096},
                    title="Synthetic month event",
                    start_date=date(2031, 2, 28),
                    end_date=date(2031, 3, 10),
                    category_id=17,
                ),
            ],
        )

    async def get_day(self, day: date) -> SkkuCalendarDay:
        self.day_arg = day
        return SkkuCalendarDay(
            date=day,
            day_name="목",
            events=[
                SkkuCalendarEvent(
                    key={"type": "skku_calendar_event", "article_no": 132093},
                    title="Synthetic day event",
                    start_date=date(2031, 1, 24),
                    end_date=date(2031, 2, 19),
                    category_id=17,
                ),
            ],
        )


class FailingRootCalendarService(FakeRootCalendarService):
    async def get_month(self, year: int, month: int) -> SkkuCalendarMonth:
        raise SkkuFetchError("calendar upstream unavailable")


class SkkuCalendarRootRouterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        app.dependency_overrides.clear()

    async def test_month_uses_service_dependency(self) -> None:
        fake = FakeRootCalendarService()

        async def override_service() -> FakeRootCalendarService:
            return fake

        app.dependency_overrides[get_root_calendar_service] = override_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/skku/calendar/root/month?year=2031&month=3")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(fake.month_args, (2031, 3))
        payload = response.json()
        self.assertEqual(payload["year"], 2031)
        self.assertEqual(payload["month"], 3)
        self.assertEqual(payload["events"][0]["key"]["type"], "skku_calendar_event")
        self.assertEqual(payload["events"][0]["start_date"], "2031-02-28")

    async def test_day_uses_service_dependency(self) -> None:
        fake = FakeRootCalendarService()

        async def override_service() -> FakeRootCalendarService:
            return fake

        app.dependency_overrides[get_root_calendar_service] = override_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/skku/calendar/root/days/2031-02-04")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(fake.day_arg, date(2031, 2, 4))
        payload = response.json()
        self.assertEqual(payload["date"], "2031-02-04")
        self.assertEqual(payload["day_name"], "목")
        self.assertEqual(payload["events"][0]["end_date"], "2031-02-19")

    async def test_invalid_month_returns_validation_error(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/skku/calendar/root/month?year=2031&month=13")

        self.assertEqual(response.status_code, 422)

    async def test_invalid_day_returns_validation_error(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/skku/calendar/root/days/not-a-date")

        self.assertEqual(response.status_code, 422)

    async def test_upstream_errors_return_bad_gateway(self) -> None:
        async def override_service() -> FailingRootCalendarService:
            return FailingRootCalendarService()

        app.dependency_overrides[get_root_calendar_service] = override_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/skku/calendar/root/month?year=2031&month=2")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "calendar upstream unavailable")

    async def test_openapi_contains_calendar_routes(self) -> None:
        paths = app.openapi()["paths"]

        self.assertIn("/skku/calendar/root/month", paths)
        self.assertIn("/skku/calendar/root/days/{date}", paths)

    async def test_openapi_calendar_routes_have_single_source_tag(self) -> None:
        paths = app.openapi()["paths"]

        self.assertEqual(
            paths["/skku/calendar/root/month"]["get"]["tags"],
            ["SKKU root calendar"],
        )
        self.assertEqual(
            paths["/skku/calendar/root/days/{date}"]["get"]["tags"],
            ["SKKU root calendar"],
        )


if __name__ == "__main__":
    unittest.main()
