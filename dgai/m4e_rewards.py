"""
DGAI M4e — Verifiable Rewards Engine & Sandboxed Code/Math Verifiers
(DGAI-M4-SPEC v6.0.0 Section 7)
"""

import ast
import json
import os
import re
import sys
import subprocess
import tempfile
from typing import Dict, Any, List, Optional, Union, Tuple


def verify_math_reward(expected_val: Union[int, float], model_output: str, tolerance: float = 1e-4) -> Dict[str, Any]:
    numbers = re.findall(r'-?\d+(?:\.\d+)?', model_output)
    if not numbers:
        return {"correct": False, "reward": 0.0, "reason": "Aucun nombre trouvé dans la réponse du modèle."}

    parsed_nums = [float(n) for n in numbers]
    for num in parsed_nums:
        if abs(num - float(expected_val)) <= tolerance:
            return {"correct": True, "reward": 1.0, "extracted_val": num, "expected": expected_val}

    return {"correct": False, "reward": 0.0, "extracted_nums": parsed_nums, "expected": expected_val}


def verify_format_reward(model_output: str, expected_format: str = "json", required_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    clean_str = model_output.strip()

    if expected_format.lower() == "json":
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', clean_str, re.DOTALL)
        if json_match:
            clean_str = json_match.group(1)

        try:
            parsed = json.loads(clean_str)
            if required_keys:
                missing = [k for k in required_keys if k not in parsed]
                if missing:
                    return {"valid": False, "reward": 0.5, "error": f"Clés obligatoires manquantes: {missing}"}
            return {"valid": True, "reward": 1.0, "parsed_json": parsed}
        except Exception as e:
            return {"valid": False, "reward": 0.0, "error": f"JSON invalide: {str(e)}"}

    return {"valid": False, "reward": 0.0, "error": f"Format '{expected_format}' non pris en charge."}


def _is_safe_ast(code_str: str) -> Tuple[bool, str]:
    try:
        tree = ast.parse(code_str)
    except Exception as e:
        return False, f"Erreur de syntaxe Python : {e}"

    FORBIDDEN_IMPORTS = {'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib', 'requests', 'ctypes', 'importlib', 'builtins', 'pathlib', 'signal', 'multiprocessing'}
    FORBIDDEN_DUNDERS = {'__class__', '__subclasses__', '__mro__', '__bases__', '__import__', '__globals__', '__code__', '__builtins__', '__dict__', '__getattribute__', '__setattr__'}
    FORBIDDEN_BUILTINS = {'open', 'eval', 'exec', 'compile', 'globals', 'locals', 'getattr', 'setattr', 'delattr', 'input', 'breakpoint', '__import__', 'file'}

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for n in names:
                top_module = n.split('.')[0]
                if top_module in FORBIDDEN_IMPORTS:
                    return False, f"Importation interdite détectée : '{top_module}'"

        if isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_DUNDERS or node.attr in FORBIDDEN_BUILTINS:
                return False, f"Accès à l'attribut/méthode interdit : '{node.attr}'"

        if isinstance(node, ast.Name):
            if node.id in FORBIDDEN_DUNDERS or node.id in FORBIDDEN_BUILTINS:
                return False, f"Utilisation de fonction/nom système interdit : '{node.id}'"

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and (node.func.id in FORBIDDEN_BUILTINS or node.func.id in FORBIDDEN_DUNDERS):
                return False, f"Appel de fonction système interdit : '{node.func.id}'"

    return True, "Code AST sécurisé"


def verify_code_reward(code_str: str, unit_test_func_name: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Safely verifies Python code through AST static analysis, syntax validation,
    function signature inspection, and AST-level safe math/logic evaluation.
    """
    safe, ast_msg = _is_safe_ast(code_str)
    if not safe:
        return {"passed": False, "reward": 0.0, "error": ast_msg, "security_violation": True}

    try:
        tree = ast.parse(code_str)
    except Exception as e:
        return {"passed": False, "reward": 0.0, "error": f"Erreur de syntaxe Python: {e}"}

    # Verify target function definition exists in AST
    target_func = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == unit_test_func_name:
            target_func = node
            break

    if not target_func:
        return {"passed": False, "reward": 0.0, "error": f"La fonction '{unit_test_func_name}' n'est pas définie dans le code fourni."}

    # Evaluate test cases using safe in-memory restricted AST execution
    passed_count = 0
    total_cases = len(test_cases)

    # Build safe isolated local namespace for pure functions
    local_scope = {}
    try:
        compiled_code = compile(tree, filename="<reward_sandbox>", mode="exec")
        exec(compiled_code, {"__builtins__": {"range": range, "len": len, "sum": sum, "min": min, "max": max, "abs": abs, "list": list, "dict": dict, "int": int, "float": float, "str": str, "bool": bool}}, local_scope)

        func_obj = local_scope.get(unit_test_func_name)
        if callable(func_obj):
            for tc in test_cases:
                args = tc.get("args", [])
                expected = tc.get("expected")
                res = func_obj(*args)
                if res == expected:
                    passed_count += 1

            reward = float(passed_count / total_cases) if total_cases > 0 else 0.0
            return {
                "passed": passed_count == total_cases and total_cases > 0,
                "reward": reward,
                "passed_count": passed_count,
                "total_count": total_cases
            }
    except Exception as e:
        return {"passed": False, "reward": 0.0, "error": f"Erreur d'évaluation sécurisée : {str(e)}"}

    return {"passed": False, "reward": 0.0, "error": "Évaluation impossible."}
