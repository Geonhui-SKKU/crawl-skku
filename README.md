# crawl-skku

성균관대학교 공개 게시판과 학사일정 데이터를 정규화된 JSON으로 제공하는 비공식 Python 라이브러리 및 FastAPI 애플리케이션입니다.

성균관대학교가 운영하거나 보증하는 프로젝트가 아닙니다. 성균관대학교의 명칭과 상표, 원문 콘텐츠의 권리는 각 권리자에게 있습니다. 서비스 운영 시 원문 사이트의 정책을 준수하고, 과도한 요청을 보내지 마세요.

## 지원 데이터

- 성균관대학교와 아래 대학·기관의 공개 공지사항
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

| 상세 조회 | 게시판 식별자 |
| --- | --- |
| `get_post(source, article_no)` | `root` 성균관대학교, `sw` 소프트웨어융합대학, `skb_swuniv` SW중심대학사업단, `cse` 컴퓨터교육과, `sco` 융합과학대학, `ice` 정보통신대학, `ecostat` 경제대학, `biz` 경영대학, `pharm` 약학대학 |
| `get_integrated_post(source, board_id, item_id)` | `hakbu` 학부대학, `scos` 유학대학, `liberalarts` 문과대학, `sscience` 사회과학대학, `coe` 사범대학, `art` 예술대학, `biotech` 생명공학대학, `sport` 스포츠과학대학, `ics` 성균융합원 |
| `get_cscience_post(board_id, item_id)` | `cscience` 자연과학대학 |
| `get_enc_post(article_no, board_id, item_id)` | `enc` 공과대학 |

목록에서 받은 `key`의 값을 상세 조회에 전달하세요. 통합게시판에는 학부와 대학원 메뉴가 나뉜 경우 학부 공지사항을 사용하며, 화면의 `No.` 대신 실제 상세 조회에 쓰이는 `board_id`와 `item_id`를 반환합니다. 공과대학의 `key.article_no`는 기존 API와 동일하게 화면의 `No.`를 담으므로 새 글이 등록되면 바뀔 수 있습니다. 성균융합원은 현재 운영 중인 `ics.skku.edu` 공지사항을 사용합니다.

## API 서버

```bash
uv run crawl-skku serve --host 127.0.0.1 --port 8000
```

문서는 `http://127.0.0.1:8000/docs`에서 확인할 수 있습니다. API 경로는 다음과 같습니다.

```text
GET /skku/article/{source}/posts?offset=0&limit=10
GET /skku/article/{source}/posts/{article_no}          # get_post 대상
GET /skku/article/{source}/posts/{board_id}/{item_id}  # get_integrated_post 대상
GET /skku/article/enc/posts/{article_no}/{board_id}/{item_id}
GET /skku/article/cscience/posts/{board_id}/{item_id}
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
