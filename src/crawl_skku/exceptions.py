class SkkuCrawlerError(Exception):
    """Base exception for SKKU crawler failures."""


class SkkuFetchError(SkkuCrawlerError):
    """Raised when an upstream SKKU page cannot be fetched."""


class SkkuParseError(SkkuCrawlerError):
    """Raised when an upstream SKKU page does not match expected markup."""
