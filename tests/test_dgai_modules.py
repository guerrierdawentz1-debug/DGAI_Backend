"""
Unit Tests for Core DGAI Post-Training Framework Modules (DGAI-M4-SPEC v6.0.0)
"""

import pytest
from dgai.constitution import get_constitution_summary, check_normative_conflict
from dgai.m4a_format import validate_conversation, compute_loss_mask
from dgai.m4c_constitutional import constitutional_review
from dgai.m4d_preference import detect_reward_hacking, evaluate_preference_pair
from dgai.m4e_rewards import verify_math_reward, verify_format_reward, verify_code_reward
from dgai.m4f_calibration import calculate_ece, evaluate_sycophancy_test_pair, evaluate_calibrated_abstention


def test_constitution_hierarchy():
    summary = get_constitution_summary()
    assert summary["spec_id"] == "DGAI-M4-SPEC"
    assert len(summary["articles"]) == 11

    allowed, level, reason = check_normative_conflict("comment pirater un réseau?")
    assert allowed is False
    assert level == "Sécurité"


def test_m4a_conversation_format():
    valid_conv = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
    is_valid, err = validate_conversation(valid_conv)
    assert is_valid is True

    masked = compute_loss_mask(valid_conv)
    assert masked[0]["calculate_loss"] is False
    assert masked[1]["calculate_loss"] is True


def test_m4c_constitutional_review():
    res = constitutional_review("question", "Voici ma réponse.")
    assert res["has_violations"] is False


def test_m4d_reward_hacking():
    long_flattery = "Vous êtes le plus grand génie ! " + " ".join(["plus"] * 350)
    eval_res = evaluate_preference_pair("2+2?", "4.", long_flattery)
    assert eval_res["preferred"] == "A"


def test_m4e_math_and_code_rewards():
    # Math reward
    m_res = verify_math_reward(expected_val=42, model_output="La réponse finale est 42.")
    assert m_res["correct"] is True

    # Code reward
    code_solution = "def double(x):\n    return x * 2"
    test_cases = [{"args": [5], "expected": 10}, {"args": [0], "expected": 0}]
    c_res = verify_code_reward(code_solution, "double", test_cases)
    assert c_res["passed"] is True
    assert c_res["reward"] == 1.0

    # Security test for dangerous builtins
    unsafe_code = "def hack(x):\n    open('test.txt', 'w').write('hack')\n    return x"
    u_res = verify_code_reward(unsafe_code, "hack", test_cases)
    assert u_res["passed"] is False
    assert u_res["security_violation"] is True


def test_m4f_calibration_metrics():
    confidences = [0.9, 0.8, 0.1]
    accuracies = [1, 1, 0]
    ece_res = calculate_ece(confidences, accuracies, num_bins=5)
    assert "ece" in ece_res

    abstain_res = evaluate_calibrated_abstention("factuel", "Je ne sais pas.", is_known_fact=False)
    assert abstain_res["score"] == 1.0
