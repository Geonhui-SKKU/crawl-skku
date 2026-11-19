"""Public department boards using the standard numbered SKKU CMS template."""

from crawl_skku.article import biopharm
from crawl_skku.article.bio.service import BioArticlePostService
from crawl_skku.article.board_service import NumberedArticleBoard
from crawl_skku.article.cal.service import CalArticlePostService
from crawl_skku.article.chem.service import ChemArticlePostService
from crawl_skku.article.cms import NumberedCmsBoard
from crawl_skku.article.does.service import DoesArticlePostService
from crawl_skku.article.nano.service import NanoArticlePostService

STANDARD_DEPARTMENT_BOARDS = {
    source: NumberedCmsBoard(source, url)
    for source, url in {
        # Literature
        "korean": "https://skb.skku.edu/korean/community/under_notice.do",
        "english": "https://skb.skku.edu/english/notice.do",
        "french": "https://skb.skku.edu/french/community/notice.do",
        "chinese": "https://skb.skku.edu/chinese/undergraduate_notice.do",
        "german": "https://skb.skku.edu/german/04_Community/notice.do",
        "russian": "https://russian.skku.edu/russian/deptnews.do",
        "klcc": "https://skb.skku.edu/klcc/community/under_notice.do",
        "history": "https://history.skku.edu/history/community/under_notice.do",
        "philosophy": "https://skb.skku.edu/philosophy/community/under_notice.do",
        "lis": "https://lis.skku.edu/lis/community/under_notice.do",
        # Social sciences
        "gsg": "https://gsg.skku.edu/gsg/board/notice.do",
        "psd": "https://skb.skku.edu/psd/notice.do",
        "mediacomm": "https://mediacomm.skku.edu/mediacomm/community/notice.do",
        "soc": "https://soc.skku.edu/soc/notice.do",
        "welfare": "https://skb.skku.edu/welfare/community/notice.do",
        "psych": "https://psych.skku.edu/psy/notice_undergraduate.do",
        "consumer": "https://cf.skku.edu/skkucf/community/notice.do",
        "child": "https://skb.skku.edu/child/notice.do",
        "gld": "https://gld.skku.edu/gld/community/notice.do",
        "hsc": "https://hsc.skku.edu/hsc/notice.do",
        # Economics and business
        "stat": "https://stat.skku.edu/stat/community/under_notice.do",
        "gecon": "https://globalecon.skku.edu/gecon/notice.do",
        "bus": "https://skb.skku.edu/bus/notice.do",
        "gba": "https://globalbiz.skku.edu/gba/notice.do",
        # Education
        "edu": "https://skb.skku.edu/skku-edu/community/under_notice.do",
        "klccedu": "https://skb.skku.edu/klccedu/community/notice.do",
        "mathedu": "https://skb.skku.edu/mathedu/notice.do",
        "comedu": "https://comedu.skku.edu/comedu/notice.do",
        # Arts
        "design": "https://design.skku.edu/design/notice_dept.do",
        "dance": "https://dance.skku.edu/dance/notice.do",
        "acting": "https://acting.skku.edu/acting/notice.do",
        "fashion": "https://fashion.skku.edu/fashion/notice.do",
        # Science
        "math": "https://math.skku.edu/math/community/under_notice.do",
        "physics": "https://physics.skku.edu/physics/notice/notice.do",
        "bioconv": "https://bioconv.skku.edu/bioconv/notice.do",
        # Information and communication engineering
        "eee": "https://skb.skku.edu/eee/notice.do",
        "mcce": "https://skb.skku.edu/mcce/notice.do",
        "ase": "https://skb.skku.edu/ase/notice.do",
        "sas": "https://skb.skku.edu/sas/notice.do",
        # Engineering
        "amse": "https://amse.skku.edu/AMSE/notice.do",
        "mech": "https://mech.skku.edu/me/notice.do",
        "sme": "https://sme.skku.edu/iesys/notice.do",
        "arch": "https://arch.skku.edu/arch/NEWS/notice.do",
        "qie": "https://qie.skku.edu/qie/notice.do",
        # Biotechnology
        "foodlife": "https://skb.skku.edu/foodlife/community/notice.do",
        "biomecha": "https://skb.skku.edu/biomecha/community/notice.do",
        "gene": "https://skb.skku.edu/gene/community/under_notice.do",
        # Convergence
        "gbme": "https://gbme.skku.edu/gbme/community/under_notice.do",
        "aicon": "https://aicon.skku.edu/aicon/notice.do",
        "energy": "https://energy.skku.edu/energy/notice.do",
        "ssbat": "https://ssbat.skku.edu/ssbat/notice.do",
    }.items()
}

NUMBERED_DEPARTMENT_BOARDS: dict[str, NumberedArticleBoard] = {
    **STANDARD_DEPARTMENT_BOARDS,
    "biopharm": biopharm.board,
    "chem": ChemArticlePostService(),
    "bio": BioArticlePostService(),
    "cal": CalArticlePostService(),
    "nano": NanoArticlePostService(),
    "does": DoesArticlePostService(),
}
