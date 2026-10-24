from flask import Flask, request, jsonify
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np
import pickle
import os

from dgai.constitution import get_constitution_summary, check_normative_conflict
from dgai.m4a_format import validate_conversation, compute_loss_mask, format_tool_call
from dgai.m4b_sft import SFTExample, load_sft_corpus, deduplicate_examples, decontaminate
from dgai.m4b_data_generator import generate_sft_batch, DOMAINS
from dgai.m4c_constitutional import constitutional_review
from dgai.m4d_preference import evaluate_preference_pair, detect_reward_hacking, load_preference_pairs
from dgai.m4e_rewards import verify_math_reward, verify_format_reward, verify_code_reward
from dgai.m4f_calibration import calculate_ece, evaluate_sycophancy_test_pair, evaluate_calibrated_abstention, load_sycophancy_benchmark, load_ece_benchmark

app = Flask(__name__)

# Global variables for standard backend model
model = None
scaler_X = None
scaler_y = None
model_path = "dgai_model.pkl"
scaler_X_path = "dgai_scaler_X.pkl"
scaler_y_path = "dgai_scaler_y.pkl"
config_path = "dgai_config.json"


@app.route('/')
def root():
    return jsonify({
        "message": "DGAI Backend is running",
        "engine": "scikit-learn MLPRegressor & DGAI Post-Training Framework",
        "spec_version": "6.0.0",
        "spec_id": "DGAI-M4-SPEC",
        "status": "ready"
    })


@app.route('/api/v1/spec', methods=['GET'])
def get_spec_info():
    summary = get_constitution_summary()
    return jsonify({
        "spec_id": "DGAI-M4-SPEC",
        "version": "6.0.0",
        "constitution": summary
    })


@app.route('/api/v1/init', methods=['POST'])
def init_model():
    global model, scaler_X, scaler_y
    data = request.json or {}
    input_size = data.get('input_size', 10)
    hidden_size = data.get('hidden_size', 100)
    output_size = data.get('output_size', 1)
    learning_rate = data.get('learning_rate', 0.001)
    
    # Créer le réseau de neurones
    model = MLPRegressor(
        hidden_layer_sizes=(hidden_size, hidden_size),
        activation='relu',
        solver='adam',
        learning_rate_init=learning_rate,
        max_iter=1,
        random_state=42
    )
    
    # Initialiser les scalers
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    
    # Créer des données factices pour initialiser
    X_dummy = np.random.rand(10, input_size)
    y_dummy = np.random.rand(10, output_size)
    X_scaled = scaler_X.fit_transform(X_dummy)
    y_scaled = scaler_y.fit_transform(y_dummy)
    model.fit(X_scaled, y_scaled.ravel())
    
    return jsonify({
        "status": "success",
        "message": "Modèle MLPRegressor initialisé",
        "input_size": input_size,
        "hidden_size": hidden_size,
        "output_size": output_size
    })


@app.route('/api/v1/train', methods=['POST'])
def train_model():
    global model, scaler_X, scaler_y
    data = request.json or {}
    
    X_train = np.array(data.get('X_train', []))
    y_train = np.array(data.get('y_train', []))
    X_val = np.array(data.get('X_val', []))
    y_val = np.array(data.get('y_val', []))
    epochs = data.get('epochs', 100)
    
    if len(X_train) == 0:
        return jsonify({"error": "Données de d'entraînement vides"}), 400

    # Normaliser les données
    X_train_scaled = scaler_X.fit_transform(X_train)
    y_train_scaled = scaler_y.fit_transform(y_train)
    X_val_scaled = scaler_X.transform(X_val)
    y_val_scaled = scaler_y.transform(y_val)
    
    # Entraîner le modèle
    model.max_iter = epochs
    model.fit(X_train_scaled, y_train_scaled.ravel())
    
    # Sauvegarder le modèle
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    with open(scaler_X_path, 'wb') as f:
        pickle.dump(scaler_X, f)
    with open(scaler_y_path, 'wb') as f:
        pickle.dump(scaler_y, f)
    
    # Calculer la perte de validation
    y_val_pred_scaled = model.predict(X_val_scaled)
    y_val_pred = scaler_y.inverse_transform(y_val_pred_scaled.reshape(-1, 1))
    val_loss = np.mean((y_val - y_val_pred) ** 2)
    
    return jsonify({
        "status": "success",
        "message": "Entraînement terminé",
        "epochs": epochs,
        "validation_loss": float(val_loss)
    })


@app.route('/api/v1/predict', methods=['POST'])
def predict():
    global model, scaler_X, scaler_y
    
    # Charger le modèle s'il n'est pas en mémoire
    if model is None:
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            with open(scaler_X_path, 'rb') as f:
                scaler_X = pickle.load(f)
            with open(scaler_y_path, 'rb') as f:
                scaler_y = pickle.load(f)
        else:
            return jsonify({"error": "Aucun modèle entraîné"}), 400
    
    data = np.array(request.json['data'])
    
    # Normaliser et prédire
    data_scaled = scaler_X.transform(data)
    prediction_scaled = model.predict(data_scaled)
    prediction = scaler_y.inverse_transform(prediction_scaled.reshape(-1, 1))
    
    return jsonify({
        "status": "success",
        "predictions": prediction.tolist()
    })


# ---------------------------------------------------------
# DGAI Module M4 Endpoints
# ---------------------------------------------------------

@app.route('/api/v1/m4a/format', methods=['POST'])
def api_m4a_format():
    data = request.json or {}
    conversation = data.get("conversation", [])
    valid, message = validate_conversation(conversation)
    if not valid:
        return jsonify({"status": "invalid", "error": message}), 400

    masked_turns = compute_loss_mask(conversation)
    return jsonify({
        "status": "valid",
        "message": message,
        "masked_turns": masked_turns
    })


@app.route('/api/v1/m4b/sft/corpus', methods=['GET'])
def api_m4b_sft_corpus():
    examples = load_sft_corpus()
    return jsonify({
        "status": "success",
        "count": len(examples),
        "corpus": [ex.to_dict() for ex in examples]
    })


@app.route('/api/v1/m4b/sft/generate_corpus', methods=['POST'])
def api_m4b_sft_generate_corpus():
    data = request.json or {}
    start_index = data.get("start_index", 0)
    count = min(data.get("count", 100), 100000)  # capped batch size per HTTP response
    domain = data.get("domain")

    generated = generate_sft_batch(start_index=start_index, count=count, domain=domain)
    return jsonify({
        "status": "success",
        "start_index": start_index,
        "count": len(generated),
        "total_available_capacity": 1000000,
        "domains": DOMAINS,
        "samples": [ex.to_dict() for ex in generated]
    })


@app.route('/api/v1/m4b/sft/decontaminate', methods=['POST'])
def api_m4b_decontaminate():
    data = request.json or {}
    raw_examples = data.get("examples", [])
    eval_prompts = data.get("eval_benchmark_prompts", [])
    threshold = data.get("similarity_threshold", 0.8)

    if not raw_examples:
        sft_objs = load_sft_corpus()
    else:
        sft_objs = []
        for idx, raw in enumerate(raw_examples):
            sft_objs.append(SFTExample(
                example_id=raw.get("example_id", f"ex_{idx}"),
                conversation=raw.get("conversation", []),
                source=raw.get("source", "unknown"),
                domain=raw.get("domain", "general")
            ))

    deduped = deduplicate_examples(sft_objs)
    dedup_removed = len(sft_objs) - len(deduped)

    clean_objs, decontam_removed = decontaminate(deduped, eval_prompts, similarity_threshold=threshold)

    return jsonify({
        "status": "success",
        "original_count": len(sft_objs),
        "dedup_removed": dedup_removed,
        "decontam_removed": decontam_removed,
        "final_count": len(clean_objs),
        "clean_examples": [obj.to_dict() for obj in clean_objs]
    })


@app.route('/api/v1/m4c/constitutional/review', methods=['POST'])
def api_m4c_constitutional_review():
    data = request.json or {}
    prompt = data.get("prompt", "")
    candidate = data.get("candidate_response", "")
    review_result = constitutional_review(prompt, candidate)
    return jsonify({
        "status": "success",
        "review": review_result
    })


@app.route('/api/v1/m4d/preferences/evaluate', methods=['POST'])
def api_m4d_preferences_evaluate():
    data = request.json or {}
    prompt = data.get("prompt", "")
    response_a = data.get("response_a", "")
    response_b = data.get("response_b", "")

    result = evaluate_preference_pair(prompt, response_a, response_b)
    return jsonify({
        "status": "success",
        "evaluation": result
    })


@app.route('/api/v1/m4e/rewards/verify', methods=['POST'])
def api_m4e_rewards_verify():
    data = request.json or {}
    task_type = data.get("task_type", "math")

    if task_type == "math":
        res = verify_math_reward(
            expected_val=data.get("expected"),
            model_output=data.get("model_output", ""),
            tolerance=data.get("tolerance", 1e-4)
        )
    elif task_type == "format":
        res = verify_format_reward(
            model_output=data.get("model_output", ""),
            expected_format=data.get("expected_format", "json"),
            required_keys=data.get("required_keys")
        )
    elif task_type == "code":
        res = verify_code_reward(
            code_str=data.get("code", ""),
            unit_test_func_name=data.get("func_name", "solution"),
            test_cases=data.get("test_cases", [])
        )
    else:
        return jsonify({"error": f"Type de tâche inconnu '{task_type}'"}), 400

    return jsonify({
        "status": "success",
        "task_type": task_type,
        "result": res
    })


@app.route('/api/v1/m4f/metrics/ece', methods=['POST'])
def api_m4f_ece():
    data = request.json or {}
    confidences = data.get("confidences")
    accuracies = data.get("accuracies")
    num_bins = data.get("num_bins", 10)

    if confidences is None or accuracies is None:
        bm = load_ece_benchmark()
        confidences = bm.get("confidences", [])
        accuracies = bm.get("accuracies", [])
        num_bins = bm.get("num_bins", num_bins)

    res = calculate_ece(confidences, accuracies, num_bins=num_bins)
    return jsonify({
        "status": "success",
        "metrics": res
    })


@app.route('/api/v1/m4f/sycophancy/benchmark', methods=['GET'])
def api_m4f_sycophancy_benchmark():
    bm = load_sycophancy_benchmark()
    return jsonify({
        "status": "success",
        "count": len(bm),
        "benchmark_items": bm
    })


@app.route('/api/v1/m4f/sycophancy/evaluate', methods=['POST'])
def api_m4f_sycophancy():
    data = request.json or {}
    res = evaluate_sycophancy_test_pair(
        neutral_prompt=data.get("neutral_prompt", ""),
        neutral_response=data.get("neutral_response", ""),
        pressure_prompt=data.get("pressure_prompt", ""),
        pressure_response=data.get("pressure_response", ""),
        ground_truth_fact=data.get("ground_truth_fact", "")
    )
    return jsonify({
        "status": "success",
        "evaluation": res
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
