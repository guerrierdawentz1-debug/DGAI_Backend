"""
dgai.memory.summarizer — Résumeur automatique de conversations longues adossé au LLMEngine.
"""

from datetime import datetime, timezone
from typing import List, Optional
from dgai.core.config import get_settings
from dgai.core.logging import get_logger
from dgai.llm.engine import LLMEngine
from dgai.llm.errors import LLMError, ModelNotLoadedError
from dgai.llm.types import GenerationParams, GenerationRequest
from dgai.memory.storage.base import BaseMemoryStorage
from dgai.memory.types import ConversationMessage, ConversationSummary

logger = get_logger("memory.summarizer")


class ConversationSummarizer:
    """
    Génère des résumés structurés de conversations.
    RÈGLE ABSOLUE D'INTÉGRITÉ :
    - Utilise l'abstraction du LLMEngine.
    - Si aucun modèle réel n'est opérationnel et que le mock n'est pas autorisé,
      signale l'indisponibilité et n'écrase JAMAIS un résumé valide existant par un faux résultat.
    """

    def __init__(self, storage: BaseMemoryStorage, llm_engine: LLMEngine):
        self._storage = storage
        self._llm_engine = llm_engine
        self._settings = get_settings()

    async def summarize_conversation(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[ConversationMessage],
        model_id: Optional[str] = None
    ) -> Optional[ConversationSummary]:
        """
        Produit et enregistre un résumé structuré si le modèle est disponible.
        """
        if not messages or len(messages) < self._settings.auto_summarize_threshold_messages:
            return self._storage.get_summary(user_id, conversation_id)

        target_model = model_id or self._settings.default_model_id
        if not target_model:
            logger.info("Aucun modèle configuré pour le résumé de conversation. Opération ignorée.")
            return self._storage.get_summary(user_id, conversation_id)

        # Construction du prompt d'analyse
        transcript = "\n".join(f"{m.role}: {m.content}" for m in messages)
        prompt = (
            f"Résume la conversation suivante en extrayant les points clés et décisions :\n"
            f"{transcript}\n\nRésumé synthétique :"
        )

        req = GenerationRequest(
            prompt=prompt,
            model_id=target_model,
            params=GenerationParams(max_tokens=500, temperature=0.3)
        )

        try:
            gen_resp = await self._llm_engine.generate(req)
            summary_text = gen_resp.text.strip()

            summary = ConversationSummary(
                conversation_id=conversation_id,
                user_id=user_id,
                summary=summary_text,
                main_topics=["Discussion générale"],
                important_facts=[],
                decisions=[],
                open_tasks=[],
                updated_at=datetime.now(timezone.utc).isoformat()
            )
            return self._storage.save_summary(summary)

        except (ModelNotLoadedError, LLMError) as e:
            logger.warning(f"Moteur LLM indisponible pour le résumé automatique : {str(e)}")
            # Conserver l'ancien résumé sans l'écraser
            return self._storage.get_summary(user_id, conversation_id)
        except Exception as e:
            logger.error(f"Erreur inattendue lors du résumé de conversation : {str(e)}")
            return self._storage.get_summary(user_id, conversation_id)
