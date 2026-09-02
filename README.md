# crawl-skku

성균관대학교 공개 게시판과 학사일정 데이터를 정규화된 JSON으로 제공하는 비공식 Python 라이브러리 및 FastAPI 애플리케이션입니다.

성균관대학교가 운영하거나 보증하는 프로젝트가 아닙니다. 성균관대학교의 명칭과 상표, 원문 콘텐츠의 권리는 각 권리자에게 있습니다. 서비스 운영 시 원문 사이트의 정책을 준수하고, 과도한 요청을 보내지 마세요.

## 지원 데이터

- 성균관대학교, 소프트웨어융합대학, SW중심대학사업단, 컴퓨터교육과, 융합과학대학 공지사항
- 성균관대학교 학사일정

## 설치

Python 3.11 이상과 [uv](https://docs.astral.sh/uv/)가 필요합니다.

```bash
uv sync --locked
```

## Python 사용

```python
import asyncio

from crawl_skku import CrawlSkkuClient


async def main() -> None:
    client = CrawlSkkuClient()
    posts = await client.get_posts("root", limit=10)
    print(posts[0].title)


asyncio.run(main())
```

지원 게시판 식별자는 `root`, `sw`, `skb_swuniv`, `cse`, `sco`입니다.

## API 서버

```bash
uv run crawl-skku serve --host 127.0.0.1 --port 8000
```

문서는 `http://127.0.0.1:8000/docs`에서 확인할 수 있습니다. 기존 API 경로는 다음과 같습니다.

```text
GET /skku/article/{source}/posts?offset=0&limit=10
GET /skku/article/{source}/posts/{article_no}
GET /skku/calendar/root/month?year=2026&month=7
GET /skku/calendar/root/days/{YYYY-MM-DD}
GET /healthz
```

## Docker

```bash
docker build -t crawl-skku .
docker run --rm -p 8000:8000 -v crawl-skku-data:/data crawl-skku
```

## 환경 변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `SKKU_CACHE_ENABLED` | `true` | SQLite 캐시 사용 여부 |
| `SKKU_CACHE_DIR` | `.cache/crawl-skku` | 캐시 디렉터리 |
| `SKKU_CACHE_DB_NAME` | `skku_cache.sqlite3` | 캐시 파일 이름 |
| `SKKU_CACHE_LIST_TTL_SECONDS` | `300` | 목록과 일정 캐시 TTL(초) |
| `SKKU_CACHE_DETAIL_TTL_SECONDS` | `3600` | 상세 게시글 캐시 TTL(초) |

## 개발

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run python -m unittest discover -s tests -v
```

## 라이선스

Apache-2.0 라이선스를 따릅니다. 자세한 내용은 [LICENSE.md](LICENSE.md)를 참고하세요.
