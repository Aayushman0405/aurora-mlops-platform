import os
import time
import json
import logging
import requests
import joblib
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aurora-inference")

# ---------------- Env ----------------
API_KEY = os.getenv("API_KEY")
MODEL_FETCH_BASE = os.getenv(
    "MODEL_FETCH_URL",
    "http://aurora.aurora-system.svc.cluster.local/models"
)
MODEL_NAME = os.getenv("MODEL_NAME", "california-housing")
MODEL_REF = os.getenv("MODEL_REF", "canary")
CACHE_DIR = Path(os.getenv("MODEL_CACHE_DIR", "/var/models"))

HEADERS = {"x-api-key": API_KEY}

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

MODEL_LOADED = Gauge(
    "aurora_inference_model_loaded",
    "Model loaded status"
)

model = None
model_metadata = {}

# ---------------- Schemas ----------------
class PredictionRequest(BaseModel):
    inputs: list[list[float]]

# ---------------- Security ----------------
def verify_api_key(key: str = None):
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# ---------------- Model Fetch ----------------
def fetch_model():
    global model, model_metadata

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    model_dir = CACHE_DIR / MODEL_NAME / MODEL_REF
    model_dir.mkdir(parents=True, exist_ok=True)

    meta_url = f"{MODEL_FETCH_BASE}/{MODEL_NAME}/{MODEL_REF}"
    art_url = f"{meta_url}/artifact"

    logger.info(f"Fetching metadata from {meta_url}")
    meta_resp = requests.get(meta_url, headers=HEADERS)
    meta_resp.raise_for_status()
    model_metadata = meta_resp.json()

    with open(model_dir / "metadata.json", "w") as f:
        json.dump(model_metadata, f, indent=2)

    logger.info(f"Downloading model artifact from {art_url}")
    art_resp = requests.get(art_url, headers=HEADERS, stream=True)
    art_resp.raise_for_status()

    model_path = model_dir / "model.pkl"
    with open(model_path, "wb") as f:
        for chunk in art_resp.iter_content(chunk_size=8192):
            f.write(chunk)

    logger.info(f"Loading model from {model_path}")
    model = joblib.load(model_path)
    MODEL_LOADED.set(1)

# ---------------- Startup ----------------
@app.on_event("startup")
def startup():
    try:
        fetch_model()
        logger.info("✅ Model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        MODEL_LOADED.set(0)

# ---------------- Routes ----------------
@app.get("/health")
def health():
    return {
        "status": "ok" if model else "degraded",
        "model_loaded": model is not None,
        "model_name": model_metadata.get("model_name"),
        "model_version": model_metadata.get("version"),
    }

@app.post("/predict")
def predict(req: PredictionRequest, api_key: str = Depends(verify_api_key)):
    if model is None:
        raise HTTPException(503, "Model not loaded")

    start = time.time()
    preds = model.predict(req.inputs).tolist()

    REQUEST_COUNT.labels(
        status="success",
        model_version=model_metadata.get("version", "unknown")
    ).inc()

    REQUEST_LATENCY.labels(
        model_version=model_metadata.get("version", "unknown")
    ).observe(time.time() - start)

    return {"predictions": preds}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")

