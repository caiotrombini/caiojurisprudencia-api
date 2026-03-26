from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
import re

DATE_PATTERNS = [
    '%Y-%m-%d',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M:%S.%f',
    '%d/%m/%Y',
    '%d/%m/%Y %H:%M:%S',
    '%Y%m%d',
    '%Y%m%d%H',
    '%Y%m%d%H%M',
    '%Y%m%d%H%M%S',
]

_DIGITS_ONLY = re.compile(r'^\d+$')


def _looks_like_compact_date(raw: str) -> bool:
    if len(raw) < 8 or not _DIGITS_ONLY.match(raw):
        return False
    year = int(raw[0:4])
    month = int(raw[4:6])
    day = int(raw[6:8])
    return 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31


def _parse_epoch(raw: str) -> Optional[str]:
    try:
        number = int(raw)
    except Exception:
        return None
    if len(raw) == 13:
        return datetime.fromtimestamp(number / 1000, tz=timezone.utc).date().isoformat()
    if len(raw) == 10 and 946684800 <= number <= 4102444800:
        return datetime.fromtimestamp(number, tz=timezone.utc).date().isoformat()
    return None


def normalize_date(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        raw_number = str(int(value))
        if _looks_like_compact_date(raw_number):
            return normalize_date(raw_number)
        if abs(float(value)) >= 946684800:
            try:
                timestamp = float(value) / 1000 if abs(float(value)) >= 1_000_000_000_000 else float(value)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
            except Exception:
                return None
        return None

    raw = str(value).strip()
    if not raw:
        return None

    raw = raw.replace('Z', '+00:00')
    digits = re.sub(r'\D', '', raw)

    if _DIGITS_ONLY.match(raw):
        if _looks_like_compact_date(raw):
            for length in (14, 12, 10, 8):
                if len(raw) >= length:
                    candidate = raw[:length]
                    for pattern in DATE_PATTERNS:
                        if len(candidate) == len(pattern.replace('%Y', '0000').replace('%m', '00').replace('%d', '00').replace('%H', '00').replace('%M', '00').replace('%S', '00').replace('%f', '000000')):
                            try:
                                return datetime.strptime(candidate, pattern).date().isoformat()
                            except Exception:
                                pass
            try:
                return datetime.strptime(raw[:8], '%Y%m%d').date().isoformat()
            except Exception:
                pass
        epoch = _parse_epoch(raw)
        if epoch:
            return epoch

    if digits and _looks_like_compact_date(digits):
        try:
            return datetime.strptime(digits[:8], '%Y%m%d').date().isoformat()
        except Exception:
            pass

    for pattern in DATE_PATTERNS:
        try:
            return datetime.strptime(raw, pattern).date().isoformat()
        except Exception:
            continue

    try:
        return datetime.fromisoformat(raw).date().isoformat()
    except Exception:
        return None
