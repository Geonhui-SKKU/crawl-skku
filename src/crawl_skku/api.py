from fastapi import FastAPI

from crawl_skku.article.router import router as skku_article_router
from crawl_skku.calendar.router import router as skku_calendar_router


def create_app() -> FastAPI:
    app = FastAPI(title="crawl-skku")
    app.include_router(skku_article_router, prefix="/skku/article")
    app.include_router(skku_calendar_router, prefix="/skku/calendar")

    @app.get("/healthz", tags=["서비스 상태"], summary="서비스 상태 확인")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
