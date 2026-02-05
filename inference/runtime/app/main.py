import os
import time
import logging
import json
import joblib

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aurora-inference")

# ---------------- Env ----------------
API_KEY = os.getenv("API_KEY")
MODEL_PATH = os.getenv("MODEL_PATH", "/models/california-housing/latest/model.pkl")
MODEL_VERSION_FILE = os.getenv("MODEL_VERSION_FILE", "/models/california-housing/latest/metadata.json")

# ---------------- App ----------------
app = FastAPI(title="Aurora Inference Runtime")

# ---------------- Metrics ----------------
REQUEST_COUNT = Counter(
    "aurora_inference_requests_total",
    "Total inference requests",
    ["status", "model_version"]
)

REQUEST_LATENCY = Histogram(
    "aurora_inference_request_latency_seconds",
    "Inference latency",
    ["model_version"]
)

MODEL_LOAD_TIME = Gauge(
    "aurora_inference_model_load_timestamp",
    "Timestamp when model was last loaded"
)

MODEL_VERSION = Gauge(
    "aurora_inference_model_version",
    "Model version currently loaded",
    ["model_name", "version"]
)

model = None
model_metadata = {}

# ---------------- Schemas ----------------
class PredictionRequest(BaseModel):
    inputs: List[List[float]]

class ModelInfo(BaseModel):
    name: str
    version: str
    algorithm: str
    r2_score: float
    trained_at: str
    features: int

# ---------------- Security ----------------
def verify_api_key(key: str = None):
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# ---------------- Model Loader ----------------
def load_model_metadata():
    global model_metadata
    
    if os.path.exists(MODEL_VERSION_FILE):
        try:
            with open(MODEL_VERSION_FILE, 'r') as f:
                model_metadata = json.load(f)
            logger.info(f"Loaded model metadata: {model_metadata.get('model_name')} v{model_metadata.get('version')}")
        except Exception as e:
            logger.error(f"Failed to load model metadata: {e}")
            model_metadata = {}
    else:
        logger.warning(f"Model metadata file not found: {MODEL_VERSION_FILE}")

@app.on_event("startup")
def load_model():
    global model
    
    logger.info(f"Loading model from path: {MODEL_PATH}")
    load_model_metadata()

    if not os.path.exists(MODEL_PATH):
        logger.error(f"Model file not found at {MODEL_PATH}")
        # Don't crash - allow health checks to pass but predictions will fail
        MODEL_VERSION.labels(
            model_name=model_metadata.get('model_name', 'unknown'),
            version=model_metadata.get('version', 'unknown')
        ).set(0)
        return

    try:
        start_time = time.time()
        model = joblib.load(MODEL_PATH)
        load_time = time.time() - start_time
        
        logger.info(f"✅ Model loaded successfully in {load_time:.2f}s")
        logger.info(f"✅ Model details: {model_metadata.get('model_name')} v{model_metadata.get('version')}")
        
        # Update metrics
        MODEL_LOAD_TIME.set_to_current_time()
        MODEL_VERSION.labels(
            model_name=model_metadata.get('model_name', 'unknown'),
            version=model_metadata.get('version', 'unknown')
        ).set(1)
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        MODEL_VERSION.labels(
            model_name=model_metadata.get('model_name', 'unknown'),
            version=model_metadata.get('version', 'unknown')
        ).set(0)

# ---------------- Routes ----------------
@app.get("/health")
def health():
    status = {
        "status": "ok" if model is not None else "degraded",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
        "metadata_loaded": bool(model_metadata)
    }
    
    if model_metadata:
        status.update({
            "model_name": model_metadata.get('model_name'),
            "model_version": model_metadata.get('version'),
            "r2_score": model_metadata.get('r2_score')
        })
    
    return status

@app.get("/model/info")
def model_info(api_key: str = Depends(verify_api_key)):
    if not model_metadata:
        raise HTTPException(status_code=404, detail="Model metadata not available")
    
    return ModelInfo(
        name=model_metadata.get('model_name'),
        version=model_metadata.get('version'),
        algorithm=model_metadata.get('algorithm'),
        r2_score=model_metadata.get('r2_score', 0.0),
        trained_at=model_metadata.get('trained_at'),
        features=model_metadata.get('feature_count', 0)
    )

@app.post("/predict")
def predict(req: PredictionRequest, api_key: str = Depends(verify_api_key)):
    if model is None:
        REQUEST_COUNT.labels(
            status="error",
            model_version=model_metadata.get('version', 'unknown')
        ).inc()
        raise HTTPException(status_code=503, detail="Model not loaded")

    start = time.time()
    try:
        # Validate input dimensions
        if not req.inputs:
            raise HTTPException(status_code=400, detail="Empty input")
        
        expected_features = model_metadata.get('feature_count', 8)
        for i, inp in enumerate(req.inputs):
            if len(inp) != expected_features:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Input {i} has {len(inp)} features, expected {expected_features}"
                )
        
        preds = model.predict(req.inputs)
        REQUEST_COUNT.labels(
            status="success",
            model_version=model_metadata.get('version', 'unknown')
        ).inc()
        
        REQUEST_LATENCY.labels(
            model_version=model_metadata.get('version', 'unknown')
        ).observe(time.time() - start)
        
        return {"predictions": preds.tolist()}
    except Exception as e:
        REQUEST_COUNT.labels(
            status="error",
            model_version=model_metadata.get('version', 'unknown')
        ).inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")

# ---------------- Model Reload Endpoint ----------------
@app.post("/model/reload")
def reload_model(api_key: str = Depends(verify_api_key)):
    global model
    old_model = model
    model = None
    
    try:
        load_model()
        if model is not None:
            return {"status": "reloaded", "message": "Model reloaded successfully"}
        else:
            # Restore old model if reload failed
            model = old_model
            raise HTTPException(status_code=500, detail="Failed to reload model")
    except Exception as e:
        model = old_model
        raise HTTPException(status_code=500, detail=str(e))
