from flask import Flask, request, jsonify
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np
import pickle
import os

app = Flask(__name__)

# Variables globales
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
        "engine": "scikit-learn MLPRegressor",
        "status": "ready"
    })

@app.route('/api/v1/init', methods=['POST'])
def init_model():
    global model, scaler_X, scaler_y
    data = request.json
    input_size = data['input_size']
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
    model.fit(X_dummy, y_dummy)
    
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
    data = request.json
    
    X_train = np.array(data['X_train'])
    y_train = np.array(data['y_train'])
    X_val = np.array(data['X_val'])
    y_val = np.array(data['y_val'])
    epochs = data.get('epochs', 100)
    
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
