from __future__ import annotations

from fastapi import HTTPException, status

from juris_api.core.constants import SUPPORTED_TRIBUNAIS, TRIBUNAL_GROUPS


def parse_tribunais(raw: str | None) -> list[str]:
    if not raw or not raw.strip():
        return ['STF', 'STJ', 'TST', 'TJSP', 'TJRJ']
    expanded: list[str] = []
    tokens = [token.strip().upper() for token in raw.split(',') if token.strip()]
    for token in tokens:
        if token in TRIBUNAL_GROUPS:
            expanded.extend(TRIBUNAL_GROUPS[token])
        else:
            expanded.append(token)
    ordered = list(dict.fromkeys(expanded))
    invalid = [tribunal for tribunal in ordered if tribunal not in SUPPORTED_TRIBUNAIS]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'message': 'Há tribunais ou grupos não suportados na consulta.',
                'invalidos': invalid,
                'suportados': SUPPORTED_TRIBUNAIS,
                'grupos': list(TRIBUNAL_GROUPS.keys()),
            },
        )
    return ordered
