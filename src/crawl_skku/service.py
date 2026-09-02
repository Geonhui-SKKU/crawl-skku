from collections.abc import Mapping
from typing import Any

import httpx

from crawl_skku import constants
from crawl_skku.exceptions import SkkuFetchError


async def fetch_html(url: str, params: Mapping[str, Any] | None = None) -> str:
    headers = {"User-Agent": constants.DEFAULT_USER_AGENT}

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            headers=headers,
            timeout=constants.DEFAULT_TIMEOUT_SECONDS,
        ) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        raise SkkuFetchError(f"SKKU upstream returned HTTP {status_code}") from exc
    except httpx.HTTPError as exc:
        raise SkkuFetchError("Failed to fetch SKKU upstream page") from exc

    return response.text
