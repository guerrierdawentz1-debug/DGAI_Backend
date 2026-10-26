"""
DGAI M4a — Format Conversationnel & Loss Masking (DGAI-M4-SPEC v6.0.0)
"""

import json
from typing import List, Dict, Any, Tuple

VALID_ROLES = {"system", "developer", "user", "assistant", "tool"}

SPECIAL_TOKENS = {
    "BOS": "<|begin_of_text|>",
    "EOS": "<|end_of_text|>",
    "START_HEADER": "<|start_header_id|>",
    "END_HEADER": "<|end_header_id|>",
    "EOT": "<|eot_id|>"
}


def validate_message(msg: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(msg, dict):
        return False, "Le message doit être un dictionnaire JSON."
    if "role" not in msg:
        return False, "Le champ 'role' est obligatoire."
    if msg["role"] not in VALID_ROLES:
        return False, f"Rôle invalide '{msg.get('role')}'. Rôles autorisés: {sorted(list(VALID_ROLES))}"
    if "content" not in msg and "tool_calls" not in msg:
        return False, "Le message doit contenir du contenu ('content') ou des appels d'outils ('tool_calls')."
    return True, "Valid"


def validate_conversation(conversation: List[Dict[str, Any]]) -> Tuple[bool, str]:
    if not isinstance(conversation, list):
        return False, "La conversation doit être une liste de messages."
    if len(conversation) == 0:
        return False, "La conversation ne peut pas être vide."

    for idx, msg in enumerate(conversation):
        valid, err = validate_message(msg)
        if not valid:
            return False, f"Erreur au message {idx}: {err}"

    return True, "Conversation valide."


def compute_loss_mask(conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculates loss mask for tokens in conversation:
    - Target roles ('assistant', 'tool' call generation): loss_mask = 1
    - Prompt roles ('system', 'developer', 'user', 'tool' result): loss_mask = 0
    """
    masked_turns = []
    for msg in conversation:
        role = msg.get("role")
        # Target for training is assistant output and assistant tool calls
        if role in ("assistant",):
            mask_val = 1
        else:
            mask_val = 0

        content_text = str(msg.get("content", ""))
        tokens_simulated = content_text.split()

        masked_turns.append({
            "role": role,
            "content": content_text,
            "token_count": len(tokens_simulated),
            "loss_mask": mask_val,
            "masked_tokens": [mask_val] * len(tokens_simulated)
        })
    return masked_turns


def format_tool_call(tool_name: str, arguments: Dict[str, Any], call_id: str = "call_001") -> Dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": tool_name,
            "arguments": json.dumps(arguments, ensure_ascii=False)
        }
    }


def parse_tool_call(tool_call_dict: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        func = tool_call_dict.get("function", {})
        name = func.get("name")
        raw_args = func.get("arguments", "{}")
        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        return True, name, args
    except Exception as e:
        return False, f"Erreur de parsage d'outil: {str(e)}", {}
