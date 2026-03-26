from __future__ import annotations

import hashlib
import re
from typing import Any, Optional
from urllib.parse import urlparse

TOKEN_RE = re.compile(r'\w+', re.UNICODE)
_MOJIBAKE_MARKERS = ('Ã', 'Â', 'â€™', 'â€œ', 'â€', '�')


def sha256_hexdigest(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def tokenize(text: Optional[str]) -> list[str]:
    if not text:
        return []
    return [token.lower() for token in TOKEN_RE.findall(text) if len(token) >= 2]


def fix_mojibake(text: Optional[str]) -> Optional[str]:
    if not text or not any(marker in text for marker in _MOJIBAKE_MARKERS):
        return text
    for source, target in (('latin1', 'utf-8'), ('cp1252', 'utf-8')):
        try:
            return text.encode(source).decode(target)
        except Exception:
            continue
    return text


def safe_text(value: Any, max_len: Optional[int] = None) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = fix_mojibake(text) or text
    text = re.sub(r'\s+', ' ', text).strip(' \t\n\r\x00')
    if not text:
        return None
    if max_len and len(text) > max_len:
        return text[: max_len - 1].rstrip() + '…'
    return text


def clean_url(value: Any) -> Optional[str]:
    text = safe_text(value, 2000)
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return None
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
            parsed = safe_text(name, 300)
            if parsed:
                items.append(parsed)
        else:
            parsed = safe_text(entry, 300)
            if parsed:
                items.append(parsed)
    return list(dict.fromkeys(item for item in items if item))


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
        if isinstance(value, str):
            cleaned = safe_text(value, 500)
            if cleaned:
                return cleaned
        elif isinstance(value, (int, float)):
            return str(value)
    return None


def normalize_source_system(value: Any) -> Optional[str]:
    raw = safe_text(value, 120)
    if not raw:
        return None
    lowered = raw.lower()
    mapping = {
        'saj': 'SAJ',
        'pje': 'PJe',
        'projudi': 'Projudi',
        'eproc': 'eproc',
        'apolo': 'Apolo',
        'themis': 'Themis',
        'outros': 'Outros',
        'outro': 'Outros',
        'inválido': 'Não informado',
        'invalido': 'Não informado',
        'não informado': 'Não informado',
        'nao informado': 'Não informado',
    }
    return mapping.get(lowered, raw)


def infer_document_type(*values: Any) -> Optional[str]:
    blob = ' '.join(filter(None, (safe_text(v, 400) for v in values))).lower()
    if not blob:
        return None
    rules = [
        ('acórdão', 'acordao'),
        ('acordao', 'acordao'),
        ('decisão monocrática', 'decisao_monocratica'),
        ('decisao monocratica', 'decisao_monocratica'),
        ('sentença', 'sentenca'),
        ('sentenca', 'sentenca'),
        ('despacho', 'despacho'),
        ('movimentação', 'movimentacao'),
        ('movimentacao', 'movimentacao'),
        ('cumprimento de sentença', 'processo'),
        ('incidente', 'processo'),
        ('precatório', 'processo'),
        ('precatorio', 'processo'),
        ('agravo', 'processo'),
        ('recurso', 'processo'),
    ]
    for needle, normalized in rules:
        if needle in blob:
            return normalized
    return 'processo'


def result_identifier(tribunal: str, numero_processo: Optional[str], ementa: Optional[str], fonte_nome: str) -> str:
    basis = '|'.join([tribunal, numero_processo or '', safe_text(ementa, 250) or '', fonte_nome])
    return sha256_hexdigest(basis)[:20]
