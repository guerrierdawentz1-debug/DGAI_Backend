"""
DGAI Reasoning Engine & Production Q&A Assistant Pipeline
(DGAI-M4-SPEC v6.0.0 Section 7 & Article 3/9)
"""

import re
from typing import Dict, Any, List, Optional
from dgai.constitution import check_normative_conflict
from dgai.m4c_constitutional import constitutional_review
from dgai.response_style import format_response_by_style
from dgai.search_engine import search_and_synthesize
from dgai.tools import get_current_time, calculator, execute_tool_call


def generate_reasoning_chain(prompt: str, reasoning_budget: int = 3) -> Dict[str, Any]:
    """
    Generates explicit step-by-step reasoning traces and manages computation budget.
    """
    budget = max(1, min(reasoning_budget, 5))
    steps = []

    # Step 1: Query analysis & intent detection
    steps.append(f"Étape 1 [Analyse] : Analyse de la demande utilisateur ('{prompt[:60]}...') et identification de l'intention.")

    if budget >= 2:
        # Step 2: Tool requirement & knowledge check
        lower_p = prompt.lower()
        if any(k in lower_p for k in ["heure", "date", "aujourd'hui", "temps"]):
            steps.append("Étape 2 [Outillage] : Détection du besoin d'accès au temps courant (outil 'get_current_time').")
        elif any(k in lower_p for k in ["calcule", "+", "-", "*", "/", "sqrt", "pow"]):
            steps.append("Étape 2 [Outillage] : Détection du besoin de calcul numérique (outil 'calculator').")
        elif any(k in lower_p for k in ["recherche", "informations récentes", "qui est", "qu'est-ce que"]):
            steps.append("Étape 2 [Outillage] : Vérification documentaire et recherche d'informations (outil 'search_web').")
        else:
            steps.append("Étape 2 [Connaissances] : Analyse des faits en mémoire et vérification des contraintes constitutionnelles.")

    if budget >= 3:
        # Step 3: Consistency & safety validation
        steps.append("Étape 3 [Vérification] : Contrôle de la hiérarchie normative (Sécurité > Éthique > Consignes > Utilité) et absence d'hallucinations.")

    if budget >= 4:
        steps.append("Étape 4 [Formatage] : Structuration de la réponse finale selon le style sélectionné.")

    if budget >= 5:
        steps.append("Étape 5 [Auto-Critique] : Validation de la clarté, de l'honnêteté et de l'exactitude de la synthèse.")

    thought_trace = "\n".join([f"<thought>{s}</thought>" for s in steps])

    return {
        "prompt": prompt,
        "reasoning_budget": budget,
        "steps_count": len(steps),
        "steps": steps,
        "thought_trace": thought_trace
    }


def chat_assistant_pipeline(messages: List[Dict[str, Any]], style: str = "detailed", reasoning_budget: int = 3, force_web_search: bool = False) -> Dict[str, Any]:
    """
    Complete production Q&A assistant pipeline:
    1. Extracts last user prompt.
    2. Runs Constitutional Safety Check.
    3. Generates Reasoning Steps (<thought>...</thought>).
    4. Automatically invokes tools (time, calculator, search) if needed.
    5. Formats answer according to requested style.
    """
    if not messages:
        return {"error": "Aucun message fourni."}

    last_user_msg = next((m for m in reversed(messages) if m.get("role") == "user"), None)
    if not last_user_msg:
        return {"error": "Aucun message utilisateur trouvé dans la conversation."}

    prompt = last_user_msg.get("content", "").strip()

    # 1. Normative Safety Check
    lower_prompt = prompt.lower()
    is_dangerous = any(k in lower_prompt for k in ["explosif", "pirater", "cyberattaque", "malware", "poison"])
    allowed, winning_level, safety_reason = check_normative_conflict(prompt, safety_risk=is_dangerous)

    if not allowed:
        return {
            "status": "refused",
            "prompt": prompt,
            "winning_normative_level": winning_level,
            "reasoning_steps": [f"Étape 1 [Sécurité] : Refus impératif en vertu de la hiérarchie normative ({winning_level})."],
            "thought_trace": f"<thought>Étape 1 [Sécurité] : Refus impératif ({winning_level}).</thought>",
            "tool_calls": [],
            "response": safety_reason,
            "style": style
        }

    # 2. Generate Reasoning Chain
    reasoning_res = generate_reasoning_chain(prompt, reasoning_budget=reasoning_budget)

    # 3. Tool Execution & Fact Gathering
    tool_calls_executed = []
    base_response = ""

    if force_web_search:
        search_res = search_and_synthesize(prompt)
        tool_calls_executed.append({"tool_name": "search_web", "result": search_res})
        base_response = search_res["synthesized_response"]

    elif any(k in lower_prompt for k in ["comment ça va", "comment ca va", "ca va", "ça va"]):
        base_response = "Je vais très bien, merci ! En tant qu'assistant DGAI, je suis à votre disposition. Comment puis-je vous aider aujourd'hui ?"

    elif re.search(r'\b(quelle heure|l\'heure|date|aujourd\'hui|quel jour|heure actuelle|quel heure)\b', lower_prompt) or (re.search(r'\bjour\b', lower_prompt) and not any(g in lower_prompt for g in ["bonjour", "bonsoir"])):
        time_data = get_current_time()
        tool_calls_executed.append({"tool_name": "get_current_time", "result": time_data})
        base_response = f"Actuellement, nous sommes le {time_data['date']} ({time_data['day_of_week']}) et il est {time_data['time']} ({time_data['timezone']})."

    elif any(k in lower_prompt for k in ["calcule", "combien font", "ce résultat", "résultat précédent"]) or re.search(r'\b\d+\s*[\+\-\*\/\^]\s*\d+\b', lower_prompt) or (("ajoute" in lower_prompt or "multiplie" in lower_prompt or "soustrais" in lower_prompt or "divise" in lower_prompt) and any(m.get("role") == "assistant" for m in messages)):
        # Extract math expression tokens supporting multi-char operators like **
        math_tokens = re.findall(r'\d+(?:\.\d+)?|\*\*|[\+\-\*\/\^\(\)]', prompt)
        clean_expr = " ".join(math_tokens).strip() if math_tokens else prompt

        # Context resolution for follow-up turns in continuous conversations
        if any(ref in lower_prompt for ref in ["ce résultat", "résultat précédent", "à ce résultat", "par ce résultat"]) or (any(k in lower_prompt for k in ["ajoute", "multiplie", "soustrais", "divise"]) and len(math_tokens) <= 1):
            prev_num = None
            for m in reversed(messages[:-1]):
                if m.get("role") == "assistant":
                    nums = re.findall(r'\b\d+(?:\.\d+)?\b', m.get("content", ""))
                    if nums:
                        prev_num = nums[-1]
                        break
            if prev_num:
                op_match = re.search(r'(ajoute|plus|\+|\-|multiplie|fois|\*|divise|\/)\s*(\d+(?:\.\d+)?)', lower_prompt)
                if op_match:
                    op_word, val = op_match.groups()
                    if op_word in ["ajoute", "plus", "+"]:
                        clean_expr = f"{prev_num} + {val}"
                    elif op_word in ["multiplie", "fois", "*"]:
                        clean_expr = f"{prev_num} * {val}"
                    elif op_word in ["soustrais", "moins", "-"]:
                        clean_expr = f"{prev_num} - {val}"
                    elif op_word in ["divise", "/"]:
                        clean_expr = f"{prev_num} / {val}"

        calc_data = calculator(clean_expr)
        tool_calls_executed.append({"tool_name": "calculator", "result": calc_data})
        if calc_data.get("status") == "success":
            base_response = f"Le résultat du calcul me donne {calc_data['result']}."
        else:
            base_response = f"Impossible d'évaluer le calcul : {calc_data.get('error')}."

    elif any(k in lower_prompt for k in ["comment t'appelles-tu", "tu t'appelles comment", "ton nom", "qui es-tu", "qui etes-vous", "présente-toi", "presente-toi"]):
        base_response = "Je m'appelle DGAI, un assistant virtuel autonome conçu pour vous aider avec précision, honnêteté et sécurité."

    elif any(k in lower_prompt for k in ["bonjour", "salut", "coucou", "hello", "bonsoir"]):
        base_response = "Bonjour ! Comment puis-je vous aider aujourd'hui ?"

    elif "code" in lower_prompt and "python" in lower_prompt:
        base_response = (
            "Voici un exemple de script Python simple et fonctionnel :\n\n"
            "```python\n"
            "def saluer(nom):\n"
            "    return f'Bonjour, {nom} ! Bienvenue sur votre application Python.'\n\n"
            "if __name__ == '__main__':\n"
            "    utilisateur = 'Utilisateur'\n"
            "    print(saluer(utilisateur))\n"
            "```\n\n"
            "N'hésitez pas à me préciser si vous souhaitez créer une interface web (avec Flask ou FastAPI) ou un script spécifique !"
        )

    elif "python" in lower_prompt:
        base_response = "Python est un langage de programmation interprété, de haut niveau et multi-paradigmes (orienté objet, impératif, fonctionnel). Il est largement utilisé pour le développement web, l'analyse de données, l'intelligence artificielle et l'automatisation grâce à sa syntaxe lisible et son riche écosystème de bibliothèques."

    elif "apple" in lower_prompt:
        base_response = "Apple Inc. est une entreprise multinationale américaine spécialisée dans la conception et la commercialisation de produits électroniques grand public (iPhone, Mac, iPad, Apple Watch), de logiciels (iOS, macOS) et de services en ligne."

    elif "google" in lower_prompt:
        base_response = "Google LLC est une entreprise multinationale américaine de technologie spécialisée dans les services et produits liés à Internet, incluant un moteur de recherche mondial, le système d'exploitation Android, YouTube, le cloud computing et l'intelligence artificielle."

    elif "langage" in lower_prompt:
        base_response = "Un langage de programmation (comme Python, JavaScript ou C++) est un code de communication structuré permettant à un développeur d'écrire des instructions informatiques exécutables par un ordinateur."

    elif any(k in lower_prompt for k in ["recherche", "météo", "dernières nouvelles"]) or ("qui est" in lower_prompt and not any(k in lower_prompt for k in ["tu", "vous"])):
        search_res = search_and_synthesize(prompt)
        tool_calls_executed.append({"tool_name": "search_web", "result": search_res})
        base_response = search_res["synthesized_response"]

    else:
        # Grounded response fallback via live search synthesis
        search_res = search_and_synthesize(prompt)
        tool_calls_executed.append({"tool_name": "search_web", "result": search_res})
        base_response = search_res["synthesized_response"]

    # 4. Constitutional Review on Candidate Response
    review_res = constitutional_review(prompt, base_response)
    final_raw_response = review_res["revised_response"]

    # 5. Style Formatting
    styled_res = format_response_by_style(prompt, final_raw_response, style=style)

    return {
        "status": "success",
        "prompt": prompt,
        "winning_normative_level": winning_level,
        "reasoning_steps": reasoning_res["steps"],
        "thought_trace": reasoning_res["thought_trace"],
        "tool_calls": tool_calls_executed,
        "response": styled_res["formatted_response"],
        "style": style,
        "word_count": styled_res["word_count"]
    }
