from urllib.parse import urlencode

BOARD_BASE_URL = "https://skb.skku.edu/swuniv/notice.do"
BOARD_NAME = "crawl_skku.article.skb_swuniv"
DEFAULT_LIMIT = 10
MAX_LIMIT = 50


def build_detail_url(article_no: int) -> str:
    return f"{BOARD_BASE_URL}?{urlencode({'mode': 'view', 'articleNo': article_no})}"
