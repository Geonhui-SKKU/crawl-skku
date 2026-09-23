from fastapi import APIRouter

from crawl_skku.article.cscience.router import router as cscience_router
from crawl_skku.article.cse.router import router as cse_router
from crawl_skku.article.enc.router import router as enc_router
from crawl_skku.article.ice.router import router as ice_router
from crawl_skku.article.root.router import router as root_router
from crawl_skku.article.sco.router import router as sco_router
from crawl_skku.article.skb_swuniv.router import router as skb_swuniv_router
from crawl_skku.article.sw.router import router as sw_router

router = APIRouter()
router.include_router(root_router, prefix="/root")
router.include_router(sw_router, prefix="/sw")
router.include_router(skb_swuniv_router, prefix="/skb_swuniv")
router.include_router(cse_router, prefix="/cse")
router.include_router(cscience_router, prefix="/cscience")
router.include_router(sco_router, prefix="/sco")
router.include_router(enc_router, prefix="/enc")
router.include_router(ice_router, prefix="/ice")
