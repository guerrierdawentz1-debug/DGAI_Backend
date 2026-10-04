import torch
import torch.nn as nn
import torch.optim as optim
import os
import json
import numpy as np

# ==========================================
# 1. ARCHITECTURE DU MODÈLE DE NEURONES
# ==========================================
class DGAI_NeuralNetwork(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(DGAI_NeuralNetwork, self).__init__()
        self.layer1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.layer2 = nn.Linear(hidden_size, hidden_size)
        self.dropout = nn.Dropout(0.2)
        self.output_layer = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = self.layer1(x)
        x = self.relu(x)
        x = self.layer2(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.output_layer(x)
        return x

# ==========================================
# 2. MÉTHODES D'ENTRAÎNEMENT ET APPRENTISSAGE
# ==========================================
class DGAI_Trainer:
    def __init__(self, model_path="dgai_model.pth", config_path="dgai_config.json"):
        self.model_path = model_path
        self.config_path = config_path
        self.model = None
        self.criterion = nn.MSELoss()
        self.optimizer = None
        self.history = {"loss": [], "val_loss": []}

    def initialize_model(self, input_size, hidden_size, output_size, learning_rate=0.001):
        """Initialise le modèle et l'optimiseur"""
        self.model = DGAI_NeuralNetwork(input_size, hidden_size, output_size)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        config = {
            "input_size": input_size,
            "hidden_size": hidden_size,
            "output_size": output_size,
            "learning_rate": learning_rate
        }
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        return "Modèle initialisé avec succès."

    def load_model(self):
        """Charge un modèle existant depuis le disque"""
        if os.path.exists(self.model_path) and os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            self.model = DGAI_NeuralNetwork(config["input_size"], config["hidden_size"], config["output_size"])
            self.model.load_state_dict(torch.load(self.model_path))
            self.model.eval()
            self.optimizer = optim.Adam(self.model.parameters(), lr=config["learning_rate"])
            return True
        return False

    def train_model(self, X_train, y_train, X_val, y_val, epochs=100, batch_size=32):
        """Boucle d'entraînement complète avec validation"""
        if self.model is None:
            raise ValueError("Le modèle n'est pas initialisé.")
        
        self.model.train()
        X_train_t = torch.FloatTensor(X_train)
        y_train_t = torch.FloatTensor(y_train)
        X_val_t = torch.FloatTensor(X_val)
        y_val_t = torch.FloatTensor(y_val)

        for epoch in range(epochs):
            # Phase d'entraînement
            self.optimizer.zero_grad()
            outputs = self.model(X_train_t)
            loss = self.criterion(outputs, y_train_t)
            loss.backward()
            self.optimizer.step()
            
            # Phase de validation
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val_t)
                val_loss = self.criterion(val_outputs, y_val_t)
            
            self.history["loss"].append(loss.item())
            self.history["val_loss"].append(val_loss.item())
            self.model.train()

        return {"final_train_loss": loss.item(), "final_val_loss": val_loss.item()}

    def save_model(self):
        """Sauvegarde les poids du modèle"""
        if self.model:
            torch.save(self.model.state_dict(), self.model_path)
            return "Modèle sauvegardé."
        return "Aucun modèle à sauvegarder."

    def predict(self, input_data):
        """Méthode d'inférence (prédiction)"""
        if self.model is None:
            if not self.load_model():
                raise ValueError("Aucun modèle chargé ou trouvé.")
        
        self.model.eval()
        with torch.no_grad():
            tensor_input = torch.FloatTensor(input_data)
            prediction = self.model(tensor_input)
            return prediction.numpy().tolist()

# Instance globale pour l'API
dgai_brain = DGAI_Trainer()
