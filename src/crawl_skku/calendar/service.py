import json
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from crawl_skku import service as skku_service
from crawl_skku.calendar.models import UpstreamCalendarPayload
from crawl_skku.exceptions import SkkuParseError


async def fetch_calendar_payload(
    url: str,
    params: Mapping[str, Any],
) -> UpstreamCalendarPayload:
    payload = await skku_service.fetch_html(url, params=params)

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SkkuParseError("Could not parse SKKU calendar JSON") from exc

    try:
        calendar = UpstreamCalendarPayload.model_validate(data)
    except ValidationError as exc:
        raise SkkuParseError("Could not validate SKKU calendar payload") from exc

    if not calendar.success:
        raise SkkuParseError("SKKU calendar upstream response was not successful")

    return calendar
