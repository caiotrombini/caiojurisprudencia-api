from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class FonteMetadata(BaseModel):
    nome: str
    tipo: str
    oficial: bool
    endpoint: Optional[str] = None
    score_confiabilidade: float
    observacao: Optional[str] = None


class ResultadoJuridico(BaseModel):
    id_resultado: str
    tribunal: str
    numero_processo: Optional[str] = None
    classe_processual: Optional[str] = None
    assunto_principal: Optional[str] = None
    assuntos: list[str] = Field(default_factory=list)
    orgao_julgador: Optional[str] = None
    relator: Optional[str] = None
    data_julgamento: Optional[str] = None
    data_publicacao: Optional[str] = None
    ementa: Optional[str] = None
    inteiro_teor_url: Optional[str] = None
    fonte_url: Optional[str] = None
    fonte: FonteMetadata
    score_relevancia: float
    score_final: float
    metadados: dict[str, Any] = Field(default_factory=dict)


class DiagnosticoTribunal(BaseModel):
    tribunal: str
    provider: str
    status: Literal['ok', 'vazio', 'erro', 'degradado']
    resultados: int
    latencia_ms: int
    mensagem: Optional[str] = None


class ResumoBusca(BaseModel):
    search_id: str
    total_resultados: int
    tribunais_consultados: list[str]
    fontes_acionadas: list[str]
    tempo_resposta_ms: int
    cache: bool = False
    avisos: list[str] = Field(default_factory=list)


class JurisprudenciaResponse(BaseModel):
    query: str
    resumo: ResumoBusca
    diagnostico: list[DiagnosticoTribunal]
    resultados: list[ResultadoJuridico]


class HealthResponse(BaseModel):
    status: Literal['ok', 'degradado']
    versao: str
    redis: Literal['ok', 'erro']
    uptime_segundos: float
    tribunais_suportados: int
    cache_ttl_seconds: int
    rate_limit_max: int
    rate_limit_window_seconds: int


class TribunaisResponse(BaseModel):
    total: int
    grupos: dict[str, list[str]]
    todos: list[str]
