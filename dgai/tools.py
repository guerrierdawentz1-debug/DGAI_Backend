"""
DGAI Native AI Tools & Execution Engine (DGAI-M4-SPEC v6.0.0 Section 0.1 & Article 3)
"""

import ast
import operator
import datetime
import math
import sys
import os
from typing import Dict, Any, List, Optional

MAX_MATH_POWER = 1000
MAX_MATH_VALUE = 1e308

# In-memory session store
MEMORY_STORE: Dict[str, Any] = {}

TOOL_SCHEMAS = [
    {
        "name": "get_current_time",
        "description": "Retourne la date, l'heure et le jour de la semaine actuels en UTC.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "calculator",
        "description": "Évalue de manière sécurisée une expression mathématique.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "L'expression mathématique à évaluer (ex: '15 * 12 + sqrt(144)')"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "system_info",
        "description": "Obtient les informations sur l'environnement d'exécution du système DGAI.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "context_memory",
        "description": "Enregistre ou récupère des informations clés dans la mémoire de la session.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["get", "set", "list"]},
                "key": {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["action"]
        }
    }
]


DAYS_FR = {
    "Monday": "Lundi",
    "Tuesday": "Mardi",
    "Wednesday": "Mercredi",
    "Thursday": "Jeudi",
    "Friday": "Vendredi",
    "Saturday": "Samedi",
    "Sunday": "Dimanche"
}

def get_current_time() -> Dict[str, Any]:
    now = datetime.datetime.now(datetime.timezone.utc)
    day_en = now.strftime("%A")
    day_fr = DAYS_FR.get(day_en, day_en)
    return {
        "timestamp_iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": day_fr,
        "timezone": "UTC"
    }


def _eval_ast_math(node):
    operators_map = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    if isinstance(node, ast.Constant):
        val = node.value
        if isinstance(val, (int, float)):
            if abs(val) > MAX_MATH_VALUE:
                raise ValueError("Valeur numérique trop grande pour être calculée en toute sécurité.")
            return val
        raise ValueError(f"Type de constante non supporté: {type(val)}")
    elif isinstance(node, ast.BinOp):
        left = _eval_ast_math(node.left)
        right = _eval_ast_math(node.right)
        op_type = type(node.op)

        if op_type == ast.Pow:
            if abs(right) > MAX_MATH_POWER:
                raise ValueError(f"Exposant {right} trop grand (maximum autorisél: {MAX_MATH_POWER}).")

        if op_type in operators_map:
            res = operators_map[op_type](left, right)
            if isinstance(res, (int, float)) and abs(res) > MAX_MATH_VALUE:
                raise ValueError("Résultat du calcul trop grand.")
            return res
        raise ValueError(f"Opérateur binaire non supporté: {node.op}")

    elif isinstance(node, ast.UnaryOp):
        operand = _eval_ast_math(node.operand)
        op_type = type(node.op)
        if op_type in operators_map:
            return operators_map[op_type](operand)
        raise ValueError(f"Opérateur unaire non supporté: {node.op}")

    elif isinstance(node, ast.Call):
        func_name = node.func.id if isinstance(node.func, ast.Name) else None
        allowed_funcs = {
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "abs": abs,
            "round": round
        }
        if func_name in allowed_funcs:
            args = [_eval_ast_math(arg) for arg in node.args]
            return allowed_funcs[func_name](*args)
        raise ValueError(f"Fonction mathématique non autorisée: '{func_name}'")

    else:
        raise ValueError(f"Opération mathématique non autorisée ou invalide: {node}")


def calculator(expression: str) -> Dict[str, Any]:
    try:
        clean_expr = expression.strip()
        parsed = ast.parse(clean_expr, mode='eval')
        result = _eval_ast_math(parsed.body)
        return {
            "expression": expression,
            "result": result,
            "status": "success"
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e),
            "status": "error"
        }


def get_system_info() -> Dict[str, Any]:
    return {
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "environment": "Termux / Linux / Docker sandbox",
        "spec_version": "DGAI-M4-SPEC v6.0.0"
    }


def manage_context_memory(action: str, key: Optional[str] = None, value: Optional[str] = None) -> Dict[str, Any]:
    global MEMORY_STORE
    if action == "set" and key:
        MEMORY_STORE[key] = value
        return {"status": "success", "action": "set", "key": key, "value": value}
    elif action == "get" and key:
        return {"status": "success", "action": "get", "key": key, "value": MEMORY_STORE.get(key)}
    elif action == "list":
        return {"status": "success", "action": "list", "memory": MEMORY_STORE}
    return {"status": "error", "message": f"Action de mémoire invalide ou clé manquante ({action})."}


def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "get_current_time":
        return get_current_time()
    elif tool_name == "calculator":
        expr = arguments.get("expression", "")
        return calculator(expr)
    elif tool_name == "system_info":
        return get_system_info()
    elif tool_name == "context_memory":
        act = arguments.get("action", "list")
        k = arguments.get("key")
        v = arguments.get("value")
        return manage_context_memory(act, k, v)
    else:
        return {"error": f"Outil inconnu '{tool_name}'", "status": "failed"}
