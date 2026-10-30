"""
DGAI Conversational Format & Turn Specification (DGAI-M4-SPEC v6.0.0 Section 3)
"""

from typing import Dict, Any, List, Tuple, Optional

VALID_ROLES = {"system", "developer", "user", "assistant", "tool"}


def validate_message(msg: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    if not isinstance(msg, dict):
        return False, "Chaque message doit être un dictionnaire JSON."
    role = msg.get("role")
    if role not in VALID_ROLES:
        return False, f"Rôle invalide '{role}'. Les rôles valides sont : {VALID_ROLES}"
    content = msg.get("content")
    if content is None or not isinstance(content, str):
        return False, "Le champ 'content' doit être une chaîne de caractères."
    return True, None


def validate_conversation(conversation: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    if not conversation or not isinstance(conversation, list):
        return False, "La conversation doit être une liste non vide de messages."
    for idx, msg in enumerate(conversation):
        valid, err = validate_message(msg)
        if not valid:
            return False, f"Message #{idx} invalide : {err}"
    return True, None


def compute_loss_mask(conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    masked_turns = []
    for turn in conversation:
        role = turn.get("role")
        calculate_loss = (role in ["assistant", "tool"])
        masked_turns.append({
            "role": role,
            "content": turn.get("content"),
            "calculate_loss": calculate_loss
        })
    return masked_turns


def format_tool_call(tool_name: str, arguments: Dict[str, Any], call_id: str = "call_001") -> Dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": tool_name,
            "arguments": arguments
        }
    }
