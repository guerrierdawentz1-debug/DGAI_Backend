"""
DGAI M4e — Verifiable Reward Engine (DGAI-M4-SPEC v6.0.0)
"""

import ast
import json
import os
import sys
import tempfile
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Union, Tuple

FORBIDDEN_AST_NODES = (
    ast.Import,
    ast.ImportFrom,
)

FORBIDDEN_NAMES = {
    "os", "sys", "subprocess", "shutil", "importlib", "eval", "exec", "open",
    "__import__", "__builtins__", "__class__", "__subclasses__", "__mro__", "__bases__"
}


def _is_safe_ast(tree: ast.AST) -> Tuple[bool, str]:
    """
    Validates that AST contains no imports or dangerous call names / reflection access.
    """
    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_AST_NODES):
            return False, "Les instructions 'import' ne sont pas autorisées dans la sandbox de récompense."
        if isinstance(node, ast.Name) and (node.id in FORBIDDEN_NAMES or node.id.startswith("__")):
            return False, f"L'accès à '{node.id}' est interdit dans la sandbox."
        if isinstance(node, ast.Attribute) and (node.attr in FORBIDDEN_NAMES or node.attr.startswith("__")):
            return False, f"L'attribut '{node.attr}' est interdit dans la sandbox."
    return True, "Safe"


def verify_math_reward(expected_val: Union[int, float], model_output: str, tolerance: float = 1e-4) -> Dict[str, Any]:
    """
    Verifies numerical math answer extracted from response.
    """
    try:
        import re
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", model_output)
        if not numbers:
            return {"correct": False, "reward": 0.0, "extracted": None, "expected": expected_val, "reason": "Aucun nombre extrait."}

        extracted_float = float(numbers[-1])
        is_correct = abs(extracted_float - float(expected_val)) <= tolerance
        reward = 1.0 if is_correct else 0.0

        return {
            "correct": is_correct,
            "reward": reward,
            "extracted": extracted_float,
            "expected": expected_val,
            "reason": "Réponse exacte dans la tolérance." if is_correct else f"Écart supérieur à la tolérance ({tolerance})."
        }
    except Exception as e:
        return {"correct": False, "reward": 0.0, "extracted": None, "expected": expected_val, "reason": str(e)}


def verify_format_reward(model_output: str, expected_format: str = "json", required_keys: List[str] = None) -> Dict[str, Any]:
    """
    Verifies JSON or XML structural conformity.
    """
    if expected_format.lower() == "json":
        try:
            clean_output = model_output.strip()
            if "```json" in clean_output:
                clean_output = clean_output.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_output:
                clean_output = clean_output.split("```")[1].split("```")[0].strip()

            parsed = json.loads(clean_output)
            if required_keys:
                missing = [k for k in required_keys if k not in parsed]
                if missing:
                    return {"valid": False, "reward": 0.5, "reason": f"Champs obligatoires manquants: {missing}"}
            return {"valid": True, "reward": 1.0, "reason": "Format JSON valide."}
        except Exception as e:
            return {"valid": False, "reward": 0.0, "reason": f"Erreur de syntaxe JSON: {str(e)}"}

    elif expected_format.lower() == "xml":
        try:
            clean_output = model_output.strip()
            if "```xml" in clean_output:
                clean_output = clean_output.split("```xml")[1].split("```")[0].strip()
            elif "```" in clean_output:
                clean_output = clean_output.split("```")[1].split("```")[0].strip()

            ET.fromstring(clean_output)
            return {"valid": True, "reward": 1.0, "reason": "Format XML valide."}
        except Exception as e:
            return {"valid": False, "reward": 0.0, "reason": f"Erreur de syntaxe XML: {str(e)}"}

    return {"valid": False, "reward": 0.0, "reason": f"Format inconnu: {expected_format}"}


def verify_code_reward(code_str: str, unit_test_func_name: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates Python code snippet against test cases in an isolated subprocess sandbox.
    """
    try:
        # Validate function name identifier
        if not unit_test_func_name.isidentifier():
            return {
                "passed": False,
                "reward": 0.0,
                "passed_count": 0,
                "total_count": len(test_cases),
                "reason": "Nom de fonction de test invalide."
            }

        if "```python" in code_str:
            code_str = code_str.split("```python")[1].split("```")[0]
        elif "```" in code_str:
            code_str = code_str.split("```")[1].split("```")[0]

        # Parse AST & validate safety
        tree = ast.parse(code_str)
        is_safe, safety_msg = _is_safe_ast(tree)
        if not is_safe:
            return {
                "passed": False,
                "reward": 0.0,
                "passed_count": 0,
                "total_count": len(test_cases),
                "reason": f"Sécurité Sandbox: {safety_msg}"
            }

        # Safely JSON serialize variables for runner script
        encoded_test_cases = json.dumps(test_cases)
        encoded_func_name = json.dumps(unit_test_func_name)

        runner_code = (
            "import json, sys\n\n"
            + code_str
            + "\n\n"
            + "test_cases = " + encoded_test_cases + "\n"
            + "func_name = " + encoded_func_name + "\n\n"
            + "if func_name not in globals():\n"
            + "    print(json.dumps({'passed': False, 'reason': f'Fonction {func_name} non trouvée.'}))\n"
            + "    sys.exit(0)\n\n"
            + "func = globals()[func_name]\n"
            + "passed = 0\n"
            + "for tc in test_cases:\n"
            + "    inp = tc.get('input', [])\n"
            + "    exp = tc.get('output')\n"
            + "    if not isinstance(inp, list):\n"
            + "        inp = [inp]\n"
            + "    if func(*inp) == exp:\n"
            + "        passed += 1\n\n"
            + "total = len(test_cases)\n"
            + "print(json.dumps({'passed': passed == total, 'passed_count': passed, 'total_count': total, 'reason': f'{passed}/{total} tests réussis.'}))\n"
        )

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
            tmp.write(runner_code)
            tmp_path = tmp.name

        try:
            proc = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=2.0
            )
            if proc.returncode != 0:
                return {
                    "passed": False,
                    "reward": 0.0,
                    "passed_count": 0,
                    "total_count": len(test_cases),
                    "reason": f"Erreur d'exécution sandbox: {proc.stderr.strip() or proc.stdout.strip()}"
                }
            res_dict = json.loads(proc.stdout.strip())
            passed_cnt = res_dict.get("passed_count", 0)
            total_cnt = res_dict.get("total_count", len(test_cases))
            reward = passed_cnt / float(total_cnt) if total_cnt > 0 else 0.0
            return {
                "passed": res_dict.get("passed", False),
                "reward": round(reward, 2),
                "passed_count": passed_cnt,
                "total_count": total_cnt,
                "reason": res_dict.get("reason", "")
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except subprocess.TimeoutExpired:
        return {"passed": False, "reward": 0.0, "passed_count": 0, "total_count": len(test_cases), "reason": "Dépassement du temps limite (2s) dans la sandbox."}
    except Exception as e:
        return {"passed": False, "reward": 0.0, "passed_count": 0, "total_count": len(test_cases), "reason": f"Erreur d'exécution: {str(e)}"}
