"""
Tests unitaires pour le gestionnaire intelligent de contexte (dgai.reasoning.context).
"""

import pytest
from dgai.memory.types import (
    ConversationMessage,
    ConversationSummary,
    LongTermMemory,
    MemoryCategory,
)
from dgai.reasoning.context import ContextManager, estimate_tokens


def test_token_estimation():
    """Vérifie le calcul conservateur d'estimation des tokens."""
    assert estimate_tokens("") == 0
    assert estimate_tokens("Bonjour") >= 1
    assert estimate_tokens("a" * 400) == 100


def test_assemble_context_with_budget_limits():
    """Vérifie l'élagage ordonné des anciens messages pour respecter le budget."""
    ctx_mgr = ContextManager()

    messages = [
        ConversationMessage(id=f"msg-{i}", conversation_id="c1", user_id="u1", role="user", content=f"Message {i} " + ("x" * 80))
        for i in range(15)
    ]
    memories = [
        LongTermMemory(id="mem-1", user_id="u1", category=MemoryCategory.USER_PREFERENCE, content="Préfère le code commenté")
    ]
    summary = ConversationSummary(conversation_id="c1", user_id="u1", summary="Résumé des points précédents")

    # Assembler avec un budget très restreint (ex: 350 tokens)
    res = ctx_mgr.assemble_context(
        new_prompt="Que penses-tu de ma question ?",
        messages=messages,
        memories=memories,
        summary=summary,
        context_window_limit=400
    )

    assert res.estimated_tokens <= 400
    assert res.pruned_messages_count > 0
    assert len(res.warnings) > 0
    # Le dernier message doit être conservé
    assert any("Message 14" in m.content for m in res.selected_messages)


def test_context_preserves_system_instruction():
    """Vérifie que les consignes système ne sont pas altérées ni tronquées."""
    ctx_mgr = ContextManager()
    sys_inst = "CONSIGNE_SYSTEME_CRITIQUE_INVIOLABLE"

    res = ctx_mgr.assemble_context(
        new_prompt="Hello",
        system_instruction=sys_inst,
        context_window_limit=1000
    )

    assert sys_inst in res.formatted_context
    assert res.system_instruction == sys_inst
