from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

TOKEN_RE = re.compile(r'\w+', re.UNICODE)


def sha256_hexdigest(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def tokenize(text: Optional[str]) -> list[str]:
    if not text:
        return []
    return [token.lower() for token in TOKEN_RE.findall(text) if len(token) >= 2]


def safe_text(value: Any, max_len: Optional[int] = None) -> Optional[str]:
    if value is None:
        return None
    text = re.sub(r'\s+', ' ', str(value)).strip()
    if not text:
        return None
    if max_len and len(text) > max_len:
        return text[: max_len - 1].rstrip() + '…'
    return text


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def extract_name_list(value: Any) -> list[str]:
    items: list[str] = []
    for entry in ensure_list(value):
        if isinstance(entry, dict):
            name = entry.get('nome') or entry.get('descricao') or entry.get('value')
            if name:
                items.append(str(name).strip())
        elif entry:
            items.append(str(entry).strip())
    return [item for item in items if item]


def nested_get(source: dict[str, Any], *path: str) -> Any:
    current: Any = source
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_non_empty(*values: Any) -> Optional[str]:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return None


def result_identifier(tribunal: str, numero_processo: Optional[str], ementa: Optional[str], fonte_nome: str) -> str:
    basis = '|'.join([tribunal, numero_processo or '', safe_text(ementa, 250) or '', fonte_nome])
    return sha256_hexdigest(basis)[:20]
