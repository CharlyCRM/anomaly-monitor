"""Evalúa alertas de temperatura con las ventanas etiquetadas de NAB.

Las variables solo utilizan lecturas disponibles en cada momento.
La evaluación no reproduce la puntuación oficial del benchmark.
"""

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
SERIES = "realKnownCause/ambient_temperature_system_failure.csv"
BASE = "https://raw.githubusercontent.com/numenta/NAB/master/"
FEATURES = ["value", "mean12", "std12", "delta"]


def load_data():
    folder = ROOT / "data"
    folder.mkdir(exist_ok=True)
    for name, url in [
        ("series.csv", BASE + "data/" + SERIES),
        ("labels.json", BASE + "labels/combined_windows.json"),
    ]:
        target = folder / name
        if not target.exists():
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            target.write_bytes(response.content)
    frame = pd.read_csv(folder / "series.csv")
    frame["timestamp"] = pd.to_datetime(frame.timestamp)
    windows = json.loads((folder / "labels.json").read_text())[SERIES]
    labels = np.zeros(len(frame), dtype=int)
    for start, end in windows:
        labels[
            (frame.timestamp >= pd.Timestamp(start))
            & (frame.timestamp <= pd.Timestamp(end))
        ] = 1
    frame["label"] = labels
    return frame, windows


def features(frame):
    result = frame.copy()
    # La ventana termina en la lectura actual; no incorpora valores futuros.
    result["mean12"] = result.value.rolling(12).mean()
    result["std12"] = result.value.rolling(12).std()
    result["delta"] = result.value.diff()
    return result.dropna().reset_index(drop=True)


def point_metrics(labels, alarms):
    return {
        "precision": float(precision_score(labels, alarms, zero_division=0)),
        "recall": float(recall_score(labels, alarms, zero_division=0)),
        "f1": float(f1_score(labels, alarms, zero_division=0)),
        "false_positives": int(((labels == 0) & alarms).sum()),
        "alerts": int(alarms.sum()),
    }


def run():
    raw, windows = load_data()
    frame = features(raw)
    fit_end, calibration_end = int(len(frame) * 0.35), int(len(frame) * 0.5)
    fit, calibration, test = (
        frame.iloc[:fit_end],
        frame.iloc[fit_end:calibration_end],
        frame.iloc[calibration_end:],
    )
    scaler = StandardScaler().fit(fit[FEATURES])
    model = IsolationForest(
        n_estimators=150, random_state=42, contamination="auto", n_jobs=2
    ).fit(scaler.transform(fit[FEATURES]))
    calibration_scores = -model.score_samples(scaler.transform(calibration[FEATURES]))
    threshold = float(np.quantile(calibration_scores, 0.99))
    scores = -model.score_samples(scaler.transform(test[FEATURES]))
    alerts = scores > threshold
    center, spread = float(fit.value.mean()), float(fit.value.std())
    baseline_scores = np.abs((test.value.to_numpy() - center) / spread)
    calibration_baseline = np.abs((calibration.value.to_numpy() - center) / spread)
    baseline_threshold = float(np.quantile(calibration_baseline, 0.99))
    baseline_alerts = baseline_scores > baseline_threshold
    evaluated_windows = []
    for start, end in windows:
        mask = (test.timestamp >= pd.Timestamp(start)) & (
            test.timestamp <= pd.Timestamp(end)
        )
        if mask.any():
            evaluated_windows.append(
                {
                    "start": start,
                    "end": end,
                    "detected": bool(alerts[mask].any()),
                    "baseline_detected": bool(baseline_alerts[mask].any()),
                }
            )
    report = {
        "source": BASE + "data/" + SERIES,
        "sha256": hashlib.sha256((ROOT / "data/series.csv").read_bytes()).hexdigest(),
        "protocol": "Chronological 35% fit, 15% calibration, 50% test. Label-free 99th percentile thresholds. Pointwise labels derived from NAB windows; not official NAB score.",
        "split": {
            "fit": len(fit),
            "calibration": len(calibration),
            "test": len(test),
            "test_start": str(test.timestamp.iloc[0]),
            "test_end": str(test.timestamp.iloc[-1]),
            "anomaly_points_fit": int(fit.label.sum()),
            "anomaly_points_calibration": int(calibration.label.sum()),
        },
        "isolation_forest": point_metrics(test.label.to_numpy(), alerts),
        "statistical_baseline": point_metrics(test.label.to_numpy(), baseline_alerts),
        "threshold": threshold,
        "windows": evaluated_windows,
        "distribution_shift_standardized_mean": float(
            (test.value.mean() - center) / spread
        ),
        "limitations": [
            "Single labelled series, no generalization claim.",
            "Window-level labels make pointwise precision/recall sensitive to window size.",
            "Unsupervised calibration can contain anomalies; contamination counts are reported.",
            "Shift indicator is descriptive; no causal diagnosis or drift significance test.",
        ],
    }
    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "scaler": scaler,
            "threshold": threshold,
            "center": center,
            "spread": spread,
        },
        out / "model.joblib",
    )
    (out / "metrics.json").write_text(json.dumps(report, indent=2))
    result = test[["timestamp", "value", "label"]].copy()
    result["score"] = scores
    result["alert"] = alerts
    result["baseline_alert"] = baseline_alerts
    result.to_csv(out / "predictions.csv", index=False)
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
