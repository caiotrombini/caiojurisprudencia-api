from __future__ import annotations

from typing import Optional

from juris_api.models.schemas import ResultadoJuridico
from juris_api.utils.text import safe_text, tokenize


def lexical_relevance(query: str, text: Optional[str], upstream_score: float = 0.0) -> float:
    query_tokens = set(tokenize(query))
    if not query_tokens or not text:
        return min(max(upstream_score / 20.0, 0.0), 1.0)
    haystack = set(tokenize(text))
    overlap = len(query_tokens.intersection(haystack)) / max(len(query_tokens), 1)
    upstream_component = min(max(upstream_score / 20.0, 0.0), 1.0)
    return round(min(1.0, overlap * 0.70 + upstream_component * 0.30), 4)


def final_score(confidence: float, relevance: float) -> float:
    return round(min(1.0, confidence * 0.60 + relevance * 0.40), 4)


def merge_results(preferred: ResultadoJuridico, other: ResultadoJuridico) -> ResultadoJuridico:
    data = preferred.model_dump()
    fallback = other.model_dump()
    for field in ['numero_processo','classe_processual','assunto_principal','orgao_julgador','relator','data_julgamento','data_publicacao','ementa','inteiro_teor_url','fonte_url']:
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
        key = f"{item.tribunal}|{item.numero_processo or ''}|{safe_text(item.ementa, 200) or ''}"
        if key in deduped:
            current = deduped[key]
            deduped[key] = merge_results(item, current) if item.score_final > current.score_final else merge_results(current, item)
        else:
            deduped[key] = item

    def sort_key(item: ResultadoJuridico) -> tuple[float, str, str]:
        date = item.data_julgamento or item.data_publicacao or '0000-00-00'
        return (item.score_final, date, item.tribunal)

    return sorted(deduped.values(), key=sort_key, reverse=True)
