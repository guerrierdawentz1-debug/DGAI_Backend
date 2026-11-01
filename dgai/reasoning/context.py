"""
dgai.reasoning.context — Gestionnaire intelligent de la fenêtre de contexte.

Prépare les informations pour le LLM en respectant les budgets de tokens,
en éliminant les redondances et en évitant les troncatures arbitraires.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from dgai.core.config import get_settings
from dgai.memory.types import ConversationMessage, ConversationSummary, LongTermMemory


class ContextAssemblyResult(BaseModel):
    """Résultat structuré de l'assemblage de contexte."""
    system_instruction: str = Field(description="Consignes système")
    formatted_context: str = Field(description="Prompt ou contexte complet assemblé")
    selected_messages: List[ConversationMessage] = Field(default_factory=list)
    injected_memories: List[LongTermMemory] = Field(default_factory=list)
    has_summary: bool = False
    estimated_tokens: int = Field(ge=0, description="Estimation de consommation de tokens")
    max_context_limit: int = Field(ge=1, description="Limite maximale de tokens autorisée")
    pruned_messages_count: int = Field(default=0, description="Nombre de messages anciens élagués")
    warnings: List[str] = Field(default_factory=list, description="Avertissements éventuels")


def estimate_tokens(text: str) -> int:
    """
    Estimation conservative du nombre de tokens (ratio ~4 caractères par token pour le français/anglais).
    Explicitement documentée comme une estimation lorsqu'aucun tokenizer BPE natif n'est chargé.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


class ContextManager:
    """
    Orchestre l'assemblage du prompt pour le modèle :
    1. Instructions système primaires (non tronquées).
    2. Souvenirs pertinents injectés comme données d'information (non-privilégiées).
    3. Résumé de conversation si existant.
    4. Historique récent des messages sélectionné selon le budget disponible.
    5. Marge de tokens réservée pour la génération de réponse.
    """

    def __init__(self):
        self._settings = get_settings()

    def assemble_context(
        self,
        new_prompt: str,
        system_instruction: Optional[str] = None,
        messages: Optional[List[ConversationMessage]] = None,
        memories: Optional[List[LongTermMemory]] = None,
        summary: Optional[ConversationSummary] = None,
        context_window_limit: Optional[int] = None
    ) -> ContextAssemblyResult:
        limit = context_window_limit or 2048
        reserve = self._settings.context_reserve_tokens
        usable_budget = max(256, limit - reserve)

        sys_prompt = system_instruction or (
            "Tu es DGAI, un assistant d'intelligence artificielle ouvert, indépendant, précis et rigoureux. "
            "Les faits issus de la mémoire utilisateur sont fournis à titre informatif."
        )

        current_tokens = estimate_tokens(sys_prompt) + estimate_tokens(new_prompt)
        warnings: List[str] = []

        # 1. Injection des souvenirs (traités comme données d'information externes)
        injected_mem: List[LongTermMemory] = []
        memory_section = ""
        if memories:
            mem_lines = []
            for m in memories:
                # Éviter l'injection d'instructions hostiles déguisées
                safe_content = m.content.replace("\n", " ").strip()
                mem_lines.append(f"- [{m.category.value}] {safe_content}")

            if mem_lines:
                cand_mem = "\nFaits mémorisés de l'utilisateur :\n" + "\n".join(mem_lines) + "\n"
                mem_tokens = estimate_tokens(cand_mem)
                if current_tokens + mem_tokens < usable_budget:
                    memory_section = cand_mem
                    current_tokens += mem_tokens
                    injected_mem = memories
                else:
                    warnings.append("Mémoires à long terme partielles en raison du budget de tokens.")

        # 2. Injection du résumé si présent
        summary_section = ""
        has_summary = False
        if summary and summary.summary:
            cand_summary = f"\nRésumé de la conversation précédente :\n{summary.summary}\n"
            sum_tokens = estimate_tokens(cand_summary)
            if current_tokens + sum_tokens < usable_budget:
                summary_section = cand_summary
                current_tokens += sum_tokens
                has_summary = True
            else:
                warnings.append("Résumé de conversation ignoré par contrainte de tokens.")

        # 3. Sélection des messages récents (de la fin vers le début pour privilégier le récent)
        selected_msgs: List[ConversationMessage] = []
        pruned_count = 0
        if messages:
            for msg in reversed(messages):
                msg_text = f"{msg.role}: {msg.content}\n"
                msg_tokens = estimate_tokens(msg_text)
                if current_tokens + msg_tokens <= usable_budget:
                    selected_msgs.insert(0, msg)
                    current_tokens += msg_tokens
                else:
                    pruned_count += 1

            if pruned_count > 0:
                warnings.append(f"{pruned_count} message(s) ancien(s) élagué(s) pour respecter la fenêtre de contexte.")

        # 4. Assemblage final
        history_section = ""
        if selected_msgs:
            history_section = "\nHistorique récent :\n" + "".join(f"{m.role}: {m.content}\n" for m in selected_msgs)

        full_context = (
            f"{sys_prompt}\n"
            f"{memory_section}"
            f"{summary_section}"
            f"{history_section}\n"
            f"user: {new_prompt}"
        )

        return ContextAssemblyResult(
            system_instruction=sys_prompt,
            formatted_context=full_context,
            selected_messages=selected_msgs,
            injected_memories=injected_mem,
            has_summary=has_summary,
            estimated_tokens=estimate_tokens(full_context),
            max_context_limit=limit,
            pruned_messages_count=pruned_count,
            warnings=warnings
        )
