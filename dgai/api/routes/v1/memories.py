"""
dgai.api.routes.v1.memories — Endpoints REST pour la gestion des souvenirs durables (Long-Term Memory).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from dgai.api.dependencies import require_permission
from dgai.api.schemas.common import APIResponse
from dgai.api.schemas.memory import (
    CreateMemoryRequest,
    MemoryResponse,
    UpdateMemoryRequest,
)
from dgai.memory.errors import MemoryNotFoundError, PrivacyViolationError
from dgai.memory.manager import get_memory_manager
from dgai.memory.types import MemoryCategory
from dgai.safety.auth import TokenData
from dgai.safety.permissions import Permission

router = APIRouter(prefix="/memories", tags=["Memories"])


@router.post("", response_model=APIResponse[MemoryResponse], status_code=status.HTTP_201_CREATED)
async def create_memory(
    body: CreateMemoryRequest,
    token_data: TokenData = Depends(require_permission(Permission.WRITE_MEMORY))
) -> APIResponse[MemoryResponse]:
    """Enregistre un souvenir durable après validation de confidentialité."""
    mem_mgr = get_memory_manager()
    try:
        mem = mem_mgr.long_term.add_memory(
            user_id=token_data.sub,
            content=body.content,
            category=body.category,
            confidence=body.confidence,
            source_conversation_id=body.source_conversation_id,
            retention_days=body.retention_days
        )
        return APIResponse[MemoryResponse](
            success=True,
            message="Souvenir enregistré avec succès.",
            data=MemoryResponse(**mem.model_dump())
        )
    except PrivacyViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=APIResponse[List[MemoryResponse]])
async def list_memories(
    category: Optional[MemoryCategory] = None,
    include_expired: bool = False,
    token_data: TokenData = Depends(require_permission(Permission.READ_MEMORY))
) -> APIResponse[List[MemoryResponse]]:
    """Liste les souvenirs actifs de l'utilisateur."""
    mem_mgr = get_memory_manager()
    memories = mem_mgr.long_term.list_memories(
        token_data.sub,
        category=category,
        include_expired=include_expired
    )
    return APIResponse[List[MemoryResponse]](
        success=True,
        data=[MemoryResponse(**m.model_dump()) for m in memories]
    )


@router.get("/{memory_id}", response_model=APIResponse[MemoryResponse])
async def get_memory(
    memory_id: str,
    token_data: TokenData = Depends(require_permission(Permission.READ_MEMORY))
) -> APIResponse[MemoryResponse]:
    """Récupère un souvenir par identifiant. Retourne 404 si introuvable ou appartenant à un tiers."""
    mem_mgr = get_memory_manager()
    try:
        mem = mem_mgr.long_term.get_memory(token_data.sub, memory_id)
        return APIResponse[MemoryResponse](
            success=True,
            data=MemoryResponse(**mem.model_dump())
        )
    except MemoryNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Souvenir introuvable : '{memory_id}'.")


@router.patch("/{memory_id}", response_model=APIResponse[MemoryResponse])
async def update_memory(
    memory_id: str,
    body: UpdateMemoryRequest,
    token_data: TokenData = Depends(require_permission(Permission.WRITE_MEMORY))
) -> APIResponse[MemoryResponse]:
    """Met à jour un souvenir existant."""
    mem_mgr = get_memory_manager()
    try:
        updated = mem_mgr.long_term.update_memory(
            user_id=token_data.sub,
            memory_id=memory_id,
            content=body.content,
            confidence=body.confidence,
            category=body.category
        )
        return APIResponse[MemoryResponse](
            success=True,
            message="Souvenir mis à jour avec succès.",
            data=MemoryResponse(**updated.model_dump())
        )
    except MemoryNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Souvenir introuvable : '{memory_id}'.")
    except (PrivacyViolationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{memory_id}", response_model=APIResponse[dict])
async def delete_memory(
    memory_id: str,
    token_data: TokenData = Depends(require_permission(Permission.DELETE_MEMORY))
) -> APIResponse[dict]:
    """Supprime définitivement un souvenir (DELETE physique)."""
    mem_mgr = get_memory_manager()
    try:
        success = mem_mgr.long_term.delete_memory(token_data.sub, memory_id)
        return APIResponse[dict](
            success=success,
            message="Souvenir supprimé définitivement.",
            data={"memory_id": memory_id}
        )
    except MemoryNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Souvenir introuvable : '{memory_id}'.")
