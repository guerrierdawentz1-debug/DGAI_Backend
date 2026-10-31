"""
dgai.api.routes.v1.chat — Endpoint d'inférence et de génération de chat.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from dgai.api.dependencies import require_permission
from dgai.api.schemas.chat import ChatChoice, ChatMessage, ChatRequest, ChatResponse
from dgai.api.schemas.common import APIResponse
from dgai.core.config import get_settings
from dgai.core.logging import get_logger
from dgai.llm.engine import get_llm_engine
from dgai.llm.errors import (
    ConcurrencyLimitExceededError,
    ModelNotFoundError,
    ModelNotLoadedError,
    ModelTimeoutError,
)
from dgai.llm.types import GenerationParams, GenerationRequest
from dgai.reasoning.router import BrainRouter, IntentAnalyzer
from dgai.safety.auth import TokenData
from dgai.safety.permissions import Permission

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger("api.chat")


@router.post("", response_model=APIResponse[ChatResponse])
async def create_chat_completion(
    request_body: ChatRequest,
    token_data: TokenData = Depends(require_permission(Permission.EXECUTE_INFERENCE))
) -> APIResponse[ChatResponse]:
    """
    Exécute une génération de chat via le moteur central LLM.
    - Exige l'authentification avec la permission 'execute:inference'.
    - Si aucun véritable modèle open-weight n'est chargé et que le mode mock n'est pas autorisé,
      retourne explicitement une erreur 503 indiquant que le moteur IA n'est pas encore disponible.
    """
    settings = get_settings()
    llm_engine = get_llm_engine()

    # 1. Extraction du dernier prompt utilisateur
    last_user_message = next(
        (m.content for m in reversed(request_body.messages) if m.role == "user"),
        None
    )
    if not last_user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La conversation doit contenir au moins un message utilisateur ('role': 'user')."
        )

    # 2. Analyse de l'intention et routage si aucun model_id n'a été spécifié
    target_model_id = request_body.model_id
    if not target_model_id:
        try:
            analysis = IntentAnalyzer.analyze(last_user_message)
            router_instance = BrainRouter(llm_engine._registry)
            selected_model = router_instance.select_model(analysis)
            target_model_id = selected_model.model_id
        except ModelNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le moteur IA de DGAI n'est pas encore opérationnel : aucun modèle n'est disponible ou chargé."
            )

    # 3. Préparation de la requête de génération
    generation_params = GenerationParams(
        temperature=request_body.temperature or settings.default_temperature,
        max_tokens=request_body.max_tokens or settings.max_generation_tokens,
        timeout_seconds=settings.llm_generation_timeout_seconds
    )

    gen_req = GenerationRequest(
        prompt=last_user_message,
        model_id=target_model_id,
        params=generation_params
    )

    # 4. Appel du moteur central avec gestion typée des erreurs
    try:
        gen_res = await llm_engine.generate(gen_req)

        chat_resp = ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            model_id=gen_res.model_id,
            engine=gen_res.engine.value,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=gen_res.text),
                    finish_reason=gen_res.finish_reason
                )
            ],
            usage=gen_res.usage.model_dump(),
            latency_seconds=gen_res.latency_seconds,
            is_mock=gen_res.is_mock
        )

        return APIResponse[ChatResponse](
            success=True,
            message="Génération complétée avec succès.",
            data=chat_resp
        )

    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ModelNotLoadedError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Le modèle '{target_model_id}' n'est pas encore initialisé ou chargé en mémoire."
        )
    except ModelTimeoutError as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except ConcurrencyLimitExceededError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la génération de chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne s'est produite lors de l'exécution de l'inférence."
        )
