from crawl_skku.article.pharm.service import PharmArticlePostService

BOARD_URL = "https://biopharm.skku.edu/bbs/board.php"
PAGE_SIZE = 15

board = PharmArticlePostService("biopharm", BOARD_URL, PAGE_SIZE)
