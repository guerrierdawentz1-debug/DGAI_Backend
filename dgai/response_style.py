"""
DGAI Response Style Controller (DGAI-M4-SPEC v6.0.0 Section 3 & 4)
"""

import re
from typing import Dict, Any, Optional


def format_response_by_style(prompt: str, raw_content: str, style: str = "detailed", max_words: Optional[int] = None) -> Dict[str, Any]:
    """
    Formats the candidate response according to requested output style:
    - 'short' / 'concise': concise direct answer
    - 'detailed' / 'long': natural thorough explanation
    - 'bullet_points': structured bulleted list
    - 'structured': JSON/XML or titled sections
    """
    style = style.lower().strip()
    clean_text = raw_content.strip()

    if style in ["short", "concise"]:
        # Extract first key sentence or short summary
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if s.strip()]
        formatted = sentences[0] if sentences else clean_text
        if len(formatted.split()) > 30:
            words = formatted.split()[:30]
            formatted = " ".join(words) + "..."

    elif style in ["detailed", "long"]:
        formatted = clean_text

    elif style == "bullet_points":
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 5]
        if sentences:
            formatted = "\n".join([f"• {s}" if not s.startswith("•") else s for s in sentences])
        else:
            formatted = f"• {clean_text}"

    elif style == "structured":
        formatted = f"### Réponse DGAI\n\n{clean_text}"

    else:
        formatted = clean_text

    if max_words and max_words > 0:
        words = formatted.split()
        if len(words) > max_words:
            formatted = " ".join(words[:max_words]) + "..."

    return {
        "style": style,
        "formatted_response": formatted,
        "word_count": len(formatted.split()),
        "max_words_applied": max_words
    }
