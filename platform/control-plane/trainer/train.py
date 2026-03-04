import os
import json
import joblib
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

MODEL_NAME = os.getenv("MODEL_NAME", "california-housing")
MODEL_VERSION = os.getenv("MODEL_VERSION")
ROOT = "/shared-models/aurora"

if not MODEL_VERSION:
    raise RuntimeError("MODEL_VERSION must be set")

def main():
    print(f"🚀 Training {MODEL_NAME} version {MODEL_VERSION}")

    X = np.random.rand(1000, 8)
    y = np.random.rand(1000)
    X_train, X_test, y_train, y_test = train_test_split(X, y)

    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)

    version_dir = f"{ROOT}/{MODEL_NAME}/versions/{MODEL_VERSION}"
    os.makedirs(version_dir, exist_ok=True)

    model_path = f"{version_dir}/model.pkl"
    joblib.dump(model, model_path)

    metadata = {
        "model_name": MODEL_NAME,
        "version": MODEL_VERSION,
        "framework": "sklearn",
        "algorithm": "random_forest",
        "r2_score": score,
        "trained_at": datetime.utcnow().isoformat(),
        "features": X.shape[1],
    }

    with open(f"{version_dir}/metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("✅ Training complete")
    print(f"📦 Saved to {version_dir}")

if __name__ == "__main__":
    main()

