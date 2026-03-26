def infer_document_type(*values: Any) -> Optional[str]:
    parts = [safe_text(v, 1200) for v in values]
    blob = ' '.join(part for part in parts if part).lower()
    if not blob:
        return None

    def has_any(*needles: str) -> bool:
        return any(needle in blob for needle in needles if needle)

    if has_any('acórdão', 'acordão', 'acordao'):
        return 'acordao'

    if has_any('decisão monocrática', 'decisao monocratica', 'monocrática', 'monocratica'):
        return 'decisao_monocratica'

    process_like_markers = (
        'cumprimento de sentença',
        'cumprimento provisório de sentença',
        'cumprimento provisorio de sentença',
        'liquidação de sentença',
        'liquidacao de sentença',
        'execução de sentença',
        'execucao de sentença',
        'execução de título',
        'execucao de titulo',
        'execução fiscal',
        'execucao fiscal',
        'procedimento comum',
        'incidente de desconsideração',
        'incidente de desconsideracao',
        'precatório',
        'precatorio',
        'requisição de pequeno valor',
        'requisicao de pequeno valor',
        'liquidação',
        'liquidacao',
    )
    if any(marker in blob for marker in process_like_markers):
        return 'processo'

    colegiado_markers = (
        'turma',
        'câmara',
        'camara',
        'seção',
        'secao',
        'órgão especial',
        'orgao especial',
        'colegiado',
        'plenário',
        'plenario',
        'pleno',
        'sessão',
        'sessao',
    )
    recursal_markers = (
        'recurso especial',
        'recurso extraordinário',
        'recurso extraordinario',
        'agravo em recurso especial',
        'agravo interno',
        'agravo regimental',
        'agravo',
        'apelação',
        'apelacao',
        'embargos de declaração',
        'embargos de declaracao',
        'embargos de divergência',
        'embargos de divergencia',
        'conflito de competência',
        'conflito de competencia',
        'mandado de segurança',
        'mandado de seguranca',
        'habeas corpus',
    )
    acordao_decision_markers = (
        'por unanimidade',
        'por maioria',
        'unanimidade',
        'negar provimento',
        'negar-lhe provimento',
        'negaram provimento',
        'dar provimento',
        'deram provimento',
        'conhecer do recurso',
        'não conhecer',
        'nao conhecer',
        'julgaram',
    )

    if any(marker in blob for marker in colegiado_markers) and any(marker in blob for marker in recursal_markers):
        return 'acordao'

    if any(marker in blob for marker in recursal_markers) and any(marker in blob for marker in acordao_decision_markers):
        return 'acordao'

    if has_any('sentença', 'sentenca'):
        return 'sentenca'

    if has_any('despacho'):
        return 'despacho'

    if has_any('movimentação', 'movimentacao', 'andamento processual', 'evento processual'):
        return 'movimentacao'

    if any(marker in blob for marker in recursal_markers):
        return 'processo'

    return 'processo'
