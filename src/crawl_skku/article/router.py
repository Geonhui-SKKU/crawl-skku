from fastapi import APIRouter

from crawl_skku.article.cse.router import router as cse_router
from crawl_skku.article.root.router import router as root_router
from crawl_skku.article.sco.router import router as sco_router
from crawl_skku.article.skb_swuniv.router import router as skb_swuniv_router
from crawl_skku.article.sw.router import router as sw_router

router = APIRouter()
router.include_router(root_router, prefix="/root")
router.include_router(sw_router, prefix="/sw")
router.include_router(skb_swuniv_router, prefix="/skb_swuniv")
router.include_router(cse_router, prefix="/cse")
router.include_router(sco_router, prefix="/sco")
