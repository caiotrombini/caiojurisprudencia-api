from __future__ import annotations

from datetime import date
from typing import Optional

from juris_api.models.schemas import ResultadoJuridico
from juris_api.utils.text import safe_text, tokenize

SUPERIOR_COURTS = {'STF', 'STJ', 'TST', 'TSE', 'STM'}


def lexical_relevance(query: str, text: Optional[str], upstream_score: float = 0.0) -> float:
    query_text = safe_text(query, 400) or ''
    query_tokens = set(tokenize(query_text))
    if not query_tokens:
        return min(max(upstream_score / 20.0, 0.0), 1.0)
    haystack_text = safe_text(text, 6000) or ''
    haystack_tokens = set(tokenize(haystack_text))
    overlap = len(query_tokens.intersection(haystack_tokens)) / max(len(query_tokens), 1)
    phrase_bonus = 0.20 if query_text.lower() in haystack_text.lower() else 0.0
    upstream_component = min(max(upstream_score / 25.0, 0.0), 1.0)
    return round(min(1.0, overlap * 0.60 + upstream_component * 0.20 + phrase_bonus), 4)


def metadata_quality(*, has_ementa: bool, has_relator: bool, has_inteiro_teor: bool, has_classe: bool, has_orgao: bool, has_assunto: bool) -> float:
    score = 0.0
    score += 0.35 if has_ementa else 0.0
    score += 0.20 if has_relator else 0.0
    score += 0.20 if has_inteiro_teor else 0.0
    score += 0.10 if has_classe else 0.0
    score += 0.10 if has_orgao else 0.0
    score += 0.05 if has_assunto else 0.0
    return round(min(score, 1.0), 4)


def recency_signal(date_iso: Optional[str]) -> float:
    if not date_iso:
        return 0.0
    try:
        year, month, day = (int(part) for part in date_iso.split('-'))
        delta_days = abs((date.today() - date(year, month, day)).days)
    except Exception:
        return 0.0
    if delta_days <= 365:
        return 1.0
    if delta_days <= 3 * 365:
        return 0.7
    if delta_days <= 8 * 365:
        return 0.45
    return 0.2


def tribunal_signal(tribunal: str) -> float:
    if tribunal in SUPERIOR_COURTS:
        return 1.0
    if tribunal.startswith('TRF') or tribunal.startswith('TRT') or tribunal.startswith('TRE'):
        return 0.75
    return 0.55


def final_score(
    confidence: float,
    relevance: float,
    *,
    metadata_score: float = 0.0,
    recency_score: float = 0.0,
    tribunal_score: float = 0.0,
) -> float:
    weighted = (
        confidence * 0.45
        + relevance * 0.30
        + metadata_score * 0.15
        + recency_score * 0.05
        + tribunal_score * 0.05
    )
    return round(min(1.0, max(0.0, weighted)), 4)


def merge_results(preferred: ResultadoJuridico, other: ResultadoJuridico) -> ResultadoJuridico:
    data = preferred.model_dump()
    fallback = other.model_dump()
    for field in ['numero_processo', 'classe_processual', 'assunto_principal', 'orgao_julgador', 'relator', 'data_julgamento', 'data_publicacao', 'ementa', 'inteiro_teor_url', 'fonte_url', 'tipo_documento']:
        if not data.get(field) and fallback.get(field):
            data[field] = fallback[field]
    if not data.get('assuntos') and fallback.get('assuntos'):
        data['assuntos'] = fallback['assuntos']
    if fallback.get('metadados'):
        data.setdefault('metadados', {})
        data['metadados'] = {**fallback['metadados'], **data['metadados']}
    if fallback.get('score_final', 0) > data.get('score_final', 0):
        data['score_final'] = fallback['score_final']
    if fallback.get('score_relevancia', 0) > data.get('score_relevancia', 0):
        data['score_relevancia'] = fallback['score_relevancia']
    if fallback.get('fonte', {}).get('score_confiabilidade', 0) > data.get('fonte', {}).get('score_confiabilidade', 0):
        data['fonte'] = fallback['fonte']
    return ResultadoJuridico(**data)


def deduplicate_results(results: list[ResultadoJuridico]) -> list[ResultadoJuridico]:
    deduped: dict[str, ResultadoJuridico] = {}
    for item in results:
        key = f"{item.tribunal}|{item.numero_processo or ''}|{safe_text(item.ementa, 200) or ''}|{item.tipo_documento or ''}"
        if key in deduped:
            current = deduped[key]
            deduped[key] = merge_results(item, current) if item.score_final > current.score_final else merge_results(current, item)
        else:
            deduped[key] = item

    def sort_key(item: ResultadoJuridico) -> tuple[float, str, float, str]:
        date_key = item.data_julgamento or item.data_publicacao or '0000-00-00'
        return (item.score_final, date_key, item.fonte.score_confiabilidade, item.tribunal)

    return sorted(deduped.values(), key=sort_key, reverse=True)
