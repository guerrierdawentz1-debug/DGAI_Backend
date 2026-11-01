"""
dgai.api.routes.v1.conversations — Endpoints REST pour la gestion des conversations et messages.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from dgai.api.dependencies import require_permission
from dgai.api.schemas.common import APIResponse
from dgai.api.schemas.memory import (
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
)
from dgai.memory.errors import ConversationNotFoundError
from dgai.memory.manager import get_memory_manager
from dgai.safety.auth import TokenData
from dgai.safety.permissions import Permission

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=APIResponse[ConversationResponse], status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: CreateConversationRequest,
    token_data: TokenData = Depends(require_permission(Permission.WRITE_MEMORY))
) -> APIResponse[ConversationResponse]:
    """Crée une nouvelle conversation pour l'utilisateur authentifié."""
    mem_mgr = get_memory_manager()
    conv = mem_mgr.conversations.create_conversation(token_data.sub, title=body.title)
    return APIResponse[ConversationResponse](
        success=True,
        message="Conversation créée avec succès.",
        data=ConversationResponse(**conv.model_dump())
    )


@router.get("", response_model=APIResponse[List[ConversationResponse]])
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    token_data: TokenData = Depends(require_permission(Permission.READ_MEMORY))
) -> APIResponse[List[ConversationResponse]]:
    """Liste les conversations appartenant exclusivement à l'utilisateur."""
    mem_mgr = get_memory_manager()
    convs = mem_mgr.conversations.list_conversations(token_data.sub, limit=limit, offset=offset)
    return APIResponse[List[ConversationResponse]](
        success=True,
        data=[ConversationResponse(**c.model_dump()) for c in convs]
    )


@router.get("/{conversation_id}", response_model=APIResponse[ConversationResponse])
async def get_conversation(
    conversation_id: str,
    token_data: TokenData = Depends(require_permission(Permission.READ_MEMORY))
) -> APIResponse[ConversationResponse]:
    """Récupère une conversation spécifique. Retourne 404 si introuvable ou appartenant à autrui."""
    mem_mgr = get_memory_manager()
    try:
        conv = mem_mgr.conversations.get_conversation(token_data.sub, conversation_id)
        return APIResponse[ConversationResponse](
            success=True,
            data=ConversationResponse(**conv.model_dump())
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation introuvable : '{conversation_id}'."
        )


@router.delete("/{conversation_id}", response_model=APIResponse[dict])
async def delete_conversation(
    conversation_id: str,
    token_data: TokenData = Depends(require_permission(Permission.DELETE_MEMORY))
) -> APIResponse[dict]:
    """Supprime définitivement une conversation et son historique."""
    mem_mgr = get_memory_manager()
    try:
        success = mem_mgr.conversations.delete_conversation(token_data.sub, conversation_id)
        return APIResponse[dict](
            success=success,
            message="Conversation et historique associés supprimés définitivement.",
            data={"conversation_id": conversation_id}
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation introuvable : '{conversation_id}'."
        )


@router.get("/{conversation_id}/messages", response_model=APIResponse[List[MessageResponse]])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    token_data: TokenData = Depends(require_permission(Permission.READ_MEMORY))
) -> APIResponse[List[MessageResponse]]:
    """Récupère les messages d'une conversation par ordre chronologique."""
    mem_mgr = get_memory_manager()
    try:
        msgs = mem_mgr.conversations.get_recent_messages(token_data.sub, conversation_id, limit=limit)
        return APIResponse[List[MessageResponse]](
            success=True,
            data=[MessageResponse(**m.model_dump()) for m in msgs]
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation introuvable : '{conversation_id}'."
        )
