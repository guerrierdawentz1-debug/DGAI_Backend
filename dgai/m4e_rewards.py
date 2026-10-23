"""
DGAI M4e — Verifiable Reward Engine (DGAI-M4-SPEC v6.0.0)
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Union


def verify_math_reward(expected_val: Union[int, float], model_output: str, tolerance: float = 1e-4) -> Dict[str, Any]:
    """
    Verifies numerical math answer extracted from response.
    """
    try:
        import re
        # Check for LaTeX boxed answer first e.g. \boxed{12} or \boxed{12.5}
        boxed_match = re.search(r"\\boxed\{([^}]+)\}", model_output)
        if boxed_match:
            candidate_str = boxed_match.group(1).strip()
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", candidate_str)
        else:
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", model_output)

        if not numbers:
            return {"correct": False, "reward": 0.0, "extracted": None, "expected": expected_val, "reason": "Aucun nombre extrait."}

        extracted_float = float(numbers[-1])  # inspect final extracted number
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
            # Extract json codeblock if present
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
    Evaluates Python code snippet against mock test cases in an isolated subprocess sandbox with timeout.
    """
    import sys
    import subprocess

    try:
        # Extract code block if wrapped in markdown
        if "```python" in code_str:
            code_str = code_str.split("```python")[1].split("```")[0]
        elif "```" in code_str:
            code_str = code_str.split("```")[1].split("```")[0]

        # Standalone script to execute in an isolated Python process
        runner_code = """
import json
import sys

code_str = """ + json.dumps(code_str) + """
func_name = """ + json.dumps(unit_test_func_name) + """
test_cases = """ + json.dumps(test_cases) + """

try:
    exec_globals = {}
    exec(code_str, exec_globals)
    if func_name not in exec_globals:
        print(json.dumps({"passed": False, "reward": 0.0, "passed_count": 0, "total_count": len(test_cases), "reason": f"Fonction {func_name} non trouvée."}))
        sys.exit(0)

    func = exec_globals[func_name]
    passed = 0
    for tc in test_cases:
        inputs = tc.get("input", [])
        expected = tc.get("output")
        if not isinstance(inputs, list):
            inputs = [inputs]
        if func(*inputs) == expected:
            passed += 1

    total = len(test_cases)
    print(json.dumps({
        "passed": passed == total,
        "reward": round(passed / float(total), 2) if total > 0 else 0.0,
        "passed_count": passed,
        "total_count": total,
        "reason": f"{passed}/{total} tests réussis."
    }))
except Exception as e:
    print(json.dumps({
        "passed": False,
        "reward": 0.0,
        "passed_count": 0,
        "total_count": len(test_cases),
        "reason": f"Erreur d'exécution: {str(e)}"
    }))
"""

        res = subprocess.run(
            [sys.executable, "-c", runner_code],
            capture_output=True,
            text=True,
            timeout=3.0
        )
        if res.returncode != 0 and not res.stdout.strip():
            return {"passed": False, "reward": 0.0, "passed_count": 0, "total_count": len(test_cases), "reason": f"Erreur d'exécution: {res.stderr.strip()}"}

        out_data = json.loads(res.stdout.strip())
        return out_data
    except subprocess.TimeoutExpired:
        return {"passed": False, "reward": 0.0, "passed_count": 0, "total_count": len(test_cases), "reason": "Dépassement du temps d'exécution (Timeout)."}
    except Exception as e:
        return {"passed": False, "reward": 0.0, "passed_count": 0, "total_count": len(test_cases), "reason": f"Erreur de sandbox: {str(e)}"}
