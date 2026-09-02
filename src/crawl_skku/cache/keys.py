import json
from collections.abc import Mapping
from typing import Any


def make_cache_key(key: Mapping[str, Any]) -> str:
    return json.dumps(key, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
