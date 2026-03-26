from __future__ import annotations

from fastapi import APIRouter, Depends

from juris_api.api.deps import require_api_key
from juris_api.core.constants import SUPPORTED_TRIBUNAIS, TRIBUNAL_GROUPS
from juris_api.models.schemas import TribunaisResponse

router = APIRouter(prefix='/v1', tags=['Meta'])


@router.get('/tribunais', response_model=TribunaisResponse, summary='Listar tribunais suportados')
async def list_tribunais(_: str = Depends(require_api_key)):
    return TribunaisResponse(total=len(SUPPORTED_TRIBUNAIS), grupos=TRIBUNAL_GROUPS, todos=SUPPORTED_TRIBUNAIS)
