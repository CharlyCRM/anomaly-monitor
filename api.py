from functools import lru_cache

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from monitor import FEATURES, ROOT, features
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="Anomaly Monitor", version="1.0.0")


class Readings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    values: list[float] = Field(min_length=12, max_length=1000)


@lru_cache
def artifact():
    file = ROOT / "artifacts/model.joblib"
    if not file.exists():
        raise HTTPException(503, "Run python monitor.py first.")
    return joblib.load(file)


@app.get("/health")
def health():
    return {"status": "ok", "model_ready": (ROOT / "artifacts/model.joblib").exists()}


@app.post("/score")
def score(readings: Readings):
    data = features(pd.DataFrame({"value": readings.values})).iloc[[-1]]
    saved = artifact()
    value = float(
        -saved["model"].score_samples(saved["scaler"].transform(data[FEATURES]))[0]
    )
    return {
        "score": value,
        "threshold": saved["threshold"],
        "alert": value > saved["threshold"],
    }
