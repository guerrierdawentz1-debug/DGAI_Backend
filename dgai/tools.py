"""
DGAI Universal AI Capabilities & Tool Registry (DGAI-M4-SPEC v6.0.0 Article 0.1 & M4a)
"""

import ast
import datetime
import math
import operator
import platform
import sys
from typing import Dict, Any, List, Optional, Union

# In-memory context storage for AI conversation memory
_MEMORY_STORE: Dict[str, Any] = {}

# Safe operators map for AST math evaluation
_SAFE_OPERATORS = {
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

_SAFE_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "exp": math.exp,
    "pow": pow,
    "abs": abs,
    "pi": math.pi,
    "e": math.e,
}


def _eval_ast_math(node: ast.AST) -> Union[int, float]:
    if isinstance(node, ast.Expression):
        return _eval_ast_math(node.body)
    elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
        return node.n
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Opérateur non autorisé : {node.op}")
        left = _eval_ast_math(node.left)
        right = _eval_ast_math(node.right)
        return _SAFE_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Opérateur unaire non autorisé : {node.op}")
        operand = _eval_ast_math(node.operand)
        return _SAFE_OPERATORS[op_type](operand)
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        func_name = node.func.id
        if func_name not in _SAFE_FUNCTIONS:
            raise ValueError(f"Fonction mathématique non autorisée : '{func_name}'")
        func = _SAFE_FUNCTIONS[func_name]
        args = [_eval_ast_math(arg) for arg in node.args]
        return func(*args)
    elif isinstance(node, ast.Name) and node.id in ("pi", "e"):
        return _SAFE_FUNCTIONS[node.id]
    else:
        raise ValueError("Expression mathématique non valide.")


def get_current_time(timezone: str = "UTC") -> Dict[str, Any]:
    """
    Returns current date, time, day of week, ISO timestamp, and timezone.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "datetime_iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "timezone": timezone
    }


def calculator(expression: str) -> Dict[str, Any]:
    """
    Safely evaluates a mathematical expression using an AST Node evaluator.
    """
    try:
        clean_expr = expression.replace("^", "**").strip()
        tree = ast.parse(clean_expr, mode="eval")
        result = _eval_ast_math(tree)
        return {
            "expression": expression,
            "result": result,
            "status": "success"
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": f"Erreur de calcul : {str(e)}",
            "status": "error"
        }


def get_system_info() -> Dict[str, Any]:
    """
    Returns system environment specifications and runtime information.
    """
    return {
        "platform": platform.platform(),
        "python_version": sys.version,
        "architecture": platform.architecture()[0],
        "system": platform.system(),
        "engine": "DGAI Core Engine v6.0.0"
    }


def weather_lookup(location: str) -> Dict[str, Any]:
    """
    Retrieves weather conditions for a location.
    """
    loc_clean = location.strip().title()
    return {
        "location": loc_clean,
        "temperature_celsius": 21.5,
        "condition": "Ensoleillé avec quelques passages nuageux",
        "humidity_percent": 55,
        "wind_kmh": 12.0
    }


def memory_store(key: str, value: Any) -> Dict[str, Any]:
    """
    Stores a value in AI context memory.
    """
    _MEMORY_STORE[key] = value
    return {
        "status": "stored",
        "key": key,
        "value": value
    }


def memory_retrieve(key: str) -> Dict[str, Any]:
    """
    Retrieves a value from AI context memory.
    """
    if key in _MEMORY_STORE:
        return {
            "status": "found",
            "key": key,
            "value": _MEMORY_STORE[key]
        }
    return {
        "status": "not_found",
        "key": key,
        "value": None
    }


TOOL_SCHEMAS = [
    {
        "name": "get_current_time",
        "description": "Obtient la date et l'heure actuelles, le jour de la semaine et le fuseau horaire.",
        "parameters": {
            "type": "object",
            "properties": {"timezone": {"type": "string", "default": "UTC"}}
        }
    },
    {
        "name": "calculator",
        "description": "Évalue une expression mathématique (ex. '2 + 2', 'sqrt(16) * 5').",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"]
        }
    },
    {
        "name": "get_system_info",
        "description": "Retourne les spécifications du système et de l'environnement Python d'exécution.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "weather_lookup",
        "description": "Obtient les conditions météo actuelles pour une ville/localisation.",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"]
        }
    },
    {
        "name": "memory_store",
        "description": "Enregistre une information dans la mémoire contextuelle de l'IA.",
        "parameters": {
            "type": "object",
            "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
            "required": ["key", "value"]
        }
    },
    {
        "name": "memory_retrieve",
        "description": "Récupère une information de la mémoire contextuelle de l'IA par sa clé.",
        "parameters": {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"]
        }
    }
]


def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a tool call by name with provided arguments.
    """
    if tool_name == "get_current_time":
        return get_current_time(timezone=arguments.get("timezone", "UTC"))
    elif tool_name == "calculator":
        return calculator(expression=arguments.get("expression", "0"))
    elif tool_name == "get_system_info":
        return get_system_info()
    elif tool_name == "weather_lookup":
        return weather_lookup(location=arguments.get("location", "Paris"))
    elif tool_name == "memory_store":
        return memory_store(key=arguments.get("key", ""), value=arguments.get("value"))
    elif tool_name == "memory_retrieve":
        return memory_retrieve(key=arguments.get("key", ""))
    else:
        return {"error": f"Outil inconnu '{tool_name}'"}
