from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
from ai_engine import dgai_brain

app = FastAPI(title="DGAI Full Stack API", version="1.0.0")

# Modèles de données pour les requêtes
class InitRequest(BaseModel):
    input_size: int
    hidden_size: int
    output_size: int
    learning_rate: Optional[float] = 0.001

class TrainRequest(BaseModel):
    X_train: List[List[float]]
    y_train: List[List[float]]
    X_val: List[List[float]]
    y_val: List[List[float]]
    epochs: Optional[int] = 50

class PredictRequest(BaseModel):
    data: List[List[float]]

@app.get("/")
def root():
    return {"message": "DGAI Backend is running. Full Stack AI Engine Ready."}

@app.post("/api/v1/init")
def init_model(req: InitRequest):
    msg = dgai_brain.initialize_model(req.input_size, req.hidden_size, req.output_size, req.learning_rate)
    return {"status": "success", "message": msg}

@app.post("/api/v1/train")
def train_model(req: TrainRequest):
    try:
        X_train = np.array(req.X_train)
        y_train = np.array(req.y_train)
        X_val = np.array(req.X_val)
        y_val = np.array(req.y_val)
        
        results = dgai_brain.train_model(X_train, y_train, X_val, y_val, epochs=req.epochs)
        dgai_brain.save_model()
        return {"status": "success", "metrics": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/predict")
def predict(req: PredictRequest):
    try:
        predictions = dgai_brain.predict(req.data)
        return {"status": "success", "predictions": predictions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
