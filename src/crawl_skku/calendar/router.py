from fastapi import APIRouter

from crawl_skku.calendar.root.router import router as root_router

router = APIRouter()
router.include_router(root_router, prefix="/root")
