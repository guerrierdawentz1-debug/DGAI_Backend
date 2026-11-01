"""
dgai.memory.retrieval — Système de recherche et de sélection des mémoires pertinentes.
"""

import re
from typing import List, Optional, Tuple
from dgai.core.config import get_settings
from dgai.memory.storage.base import BaseMemoryStorage
from dgai.memory.types import LongTermMemory


class MemoryRetriever:
    """
    Sélectionne les souvenirs pertinents pour une requête donnée.
    - Isole strictement les données de l'utilisateur.
    - Exclut les souvenirs expirés ou supprimés.
    - Applique une recherche lexicale et pondérée par mots-clés.
    - Traite le souvenir comme une donnée externe NON-PRIVILÉGIÉE (anti-injection).
    """

    def __init__(self, storage: BaseMemoryStorage):
        self._storage = storage
        self._settings = get_settings()

    def retrieve_relevant_memories(
        self,
        user_id: str,
        query: str,
        limit: Optional[int] = None
    ) -> List[LongTermMemory]:
        """
        Recherche les mémoires pertinentes pour l'utilisateur et la requête.
        """
        max_results = limit or self._settings.max_retrieved_memories
        all_memories = self._storage.list_long_term_memories(user_id, include_expired=False)

        if not all_memories:
            return []

        # Découpage des termes de la requête (mots significatifs >= 3 caractères)
        query_words = set(re.findall(r"\b\w{3,}\b", query.lower()))
        if not query_words:
            # Pas de termes discriminants : retourner les plus récentes dans la limite
            return all_memories[:max_results]

        scored: List[Tuple[float, LongTermMemory]] = []
        for mem in all_memories:
            mem_text = mem.content.lower()
            score = 0.0
            for word in query_words:
                if word in mem_text:
                    score += 1.0

            # Bonus pour les préférences explicites
            if score > 0:
                if mem.category.value == "user_preference":
                    score += 0.5
                scored.append((score, mem))

        # Trier par score décroissant, puis par date de création antéchronologique
        scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
        return [item[1] for item in scored[:max_results]]
