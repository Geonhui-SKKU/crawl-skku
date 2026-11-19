from crawl_skku.article import (
    art,
    biotech,
    biz,
    coe,
    ecostat,
    hakbu,
    ics,
    liberalarts,
    scos,
    sport,
    sscience,
)
from crawl_skku.article.cms import IntegratedCmsBoard, NumberedCmsBoard
from crawl_skku.article.pharm.service import PharmArticlePostService

NUMBERED_COLLEGE_BOARDS: dict[str, NumberedCmsBoard | PharmArticlePostService] = {
    "biz": NumberedCmsBoard("biz", biz.BOARD_URL),
    "ecostat": NumberedCmsBoard("ecostat", ecostat.BOARD_URL),
    "pharm": PharmArticlePostService(),
}

INTEGRATED_COLLEGE_BOARDS = {
    source: IntegratedCmsBoard(source, url)
    for source, url in {
        "art": art.BOARD_URL,
        "biotech": biotech.BOARD_URL,
        "coe": coe.BOARD_URL,
        "hakbu": hakbu.BOARD_URL,
        "ics": ics.BOARD_URL,
        "liberalarts": liberalarts.BOARD_URL,
        "scos": scos.BOARD_URL,
        "sport": sport.BOARD_URL,
        "sscience": sscience.BOARD_URL,
    }.items()
}
