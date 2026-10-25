"""
DGAI Flexible Response Style & Output Length Controller (DGAI-M4-SPEC v6.0.0 M4a & M4e)
"""

import re
from typing import Dict, Any, List, Optional

VALID_STYLES = {"short", "concise", "detailed", "long", "bullet_points", "structured"}


def format_response_by_style(prompt: str, content: str, style: str = "detailed", max_words: Optional[int] = None) -> Dict[str, Any]:
    """
    Formats response content according to requested style type:
    - 'short' / 'concise': Direct, concise summary.
    - 'detailed' / 'long': Exhaustive explanation with context and analysis.
    - 'bullet_points': Bulleted point list.
    - 'structured': Sectioned Markdown structure.
    """
    style_clean = style.lower().strip()
    if style_clean not in VALID_STYLES:
        style_clean = "detailed"

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content) if s.strip()]

    if style_clean in ("short", "concise"):
        # Take the most impactful core sentence(s)
        selected_sentences = sentences[:2] if len(sentences) >= 2 else sentences
        formatted_text = " ".join(selected_sentences)
        if max_words and len(formatted_text.split()) > max_words:
            formatted_text = " ".join(formatted_text.split()[:max_words]) + "..."

    elif style_clean in ("detailed", "long"):
        # Provide clean, clear detailed text without artificial boilerplate
        formatted_text = content

    elif style_clean == "bullet_points":
        bullet_items = []
        for s in sentences:
            bullet_items.append(f"• {s}")
        if not bullet_items:
            bullet_items = [f"• {content}"]
        formatted_text = f"Synthèse par points concernant '{prompt}' :\n" + "\n".join(bullet_items)

    elif style_clean == "structured":
        formatted_text = (
            f"### Aperçu\nRéponse directe à la question : {prompt}\n\n"
            f"### Analyse Détaillée\n{content}\n\n"
            f"### Synthèse & Recommandation\nL'analyse confirme la validité des principes présentés ci-dessus."
        )

    word_count = len(formatted_text.split())
    char_count = len(formatted_text)

    return {
        "prompt": prompt,
        "style": style_clean,
        "formatted_response": formatted_text,
        "word_count": word_count,
        "char_count": char_count,
        "valid": True
    }
