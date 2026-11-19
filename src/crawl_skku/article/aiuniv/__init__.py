"""AI중심대학사업단 public notices."""

from crawl_skku.article.cms import NumberedCmsBoard

SOURCE = "aiuniv"
LEGACY_SOURCE = "skb_swuniv"
BOARD_URL = "https://aiuniv.skku.edu/aiuniv/notice.do"

board = NumberedCmsBoard(SOURCE, BOARD_URL)
