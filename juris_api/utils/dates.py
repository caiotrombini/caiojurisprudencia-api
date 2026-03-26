from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

DATE_PATTERNS = [
    '%Y-%m-%d',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M:%S.%f',
    '%d/%m/%Y',
    '%d/%m/%Y %H:%M:%S',
]


def normalize_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(value).date().isoformat()
        except Exception:
            return None
    raw = str(value).strip()
    if not raw:
        return None
    raw = raw.replace('Z', '')
    for pattern in DATE_PATTERNS:
        try:
            return datetime.strptime(raw, pattern).date().isoformat()
        except Exception:
            continue
    try:
        return datetime.fromisoformat(raw).date().isoformat()
    except Exception:
        pass
    return raw[:10] if len(raw) >= 10 else raw
