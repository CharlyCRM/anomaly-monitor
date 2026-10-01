import json
import joblib
import numpy as np
import pandas as pd
import streamlit as st
from monitor import ROOT, features
from scenarios import perturb_window
from ui import init, tr, hero, require_files, line_chart, alert_chart

init("anomaly-monitor", "Anomaly Monitor")
hero("05 / ANOMALY MONITOR", tr("Cuando la señal cambia.", "When the signal changes."),
     tr("Recorre las alertas históricas y provoca un cambio sintético. Observa la respuesta de dos detectores sin volver a entrenarlos.",
        "Explore historical alerts and introduce a synthetic change. Watch two detectors respond without retraining them."))
require_files(ROOT, ["artifacts/metrics.json", "artifacts/predictions.csv", "artifacts/model.joblib", "data/series.csv"],
              "python monitor.py")
report = json.loads((ROOT / "artifacts/metrics.json").read_text())
frame = pd.read_csv(ROOT / "artifacts/predictions.csv", parse_dates=["timestamp"])
saved = joblib.load(ROOT / "artifacts/model.joblib")
raw = pd.read_csv(ROOT / "data/series.csv", parse_dates=["timestamp"])
prepared = features(raw)
fit_end, calibration_end = int(len(prepared) * .35), int(len(prepared) * .5)
# Reproduce the existing label-free baseline calibration; never fit on scenarios or test.
baseline_threshold = float(np.quantile(np.abs((prepared.iloc[fit_end:calibration_end].value.to_numpy() - saved["center"]) / saved["spread"]), .99))

with st.sidebar:
    st.markdown("### " + tr("Explorar la señal", "Explore the signal"))
    detector = st.radio("Detector", ["isolation_forest", "statistical_baseline"], key="detector",
                            format_func=lambda value: {"isolation_forest": "Isolation Forest", "statistical_baseline": "Baseline"}[value])
    window = st.slider("Puntos / Points", 48, min(576, len(frame)), 288, key="window")
    offset = st.slider("Inicio / Start", 0, max(0, len(frame) - window), 0, key="offset")

metrics = report[detector]
cols = st.columns(3)
cols[0].metric("PRECISION / TEST", f"{metrics['precision']:.3f}")
cols[1].metric("RECALL / TEST", f"{metrics['recall']:.3f}")
cols[2].metric(tr("Falsos positivos / test", "False positives / test"), metrics["false_positives"])
selected = frame.iloc[offset:offset + window].copy()
if detector == "statistical_baseline":
    selected["score"] = np.abs((selected.value - saved["center"]) / saved["spread"])
    selected["alert"] = selected.baseline_alert.astype(bool)
else:
    selected["alert"] = selected.alert.astype(bool)
threshold = saved["threshold"] if detector == "isolation_forest" else baseline_threshold

with st.container(border=True):
    st.subheader(tr("01 / Señal y alertas históricas", "01 / Historical signal and alerts"))
    alert_chart(selected)
    st.caption(tr("Línea cian: temperatura. Puntos naranjas: alertas del detector seleccionado.",
                  "Cyan line: temperature. Orange points: alerts from the selected detector."))
    score_view = selected[["timestamp", "score"]].rename(columns={"score": "Score"})
    score_view["Threshold"] = threshold
    line_chart(score_view, ["Score", "Threshold"], "Score", height=220)
    with st.expander(tr("Inspeccionar alertas", "Inspect alerts")):
        st.dataframe(selected[selected.alert], hide_index=True, width="stretch")
    st.download_button("CSV / " + tr("Ventana histórica", "Historical window"), selected.to_csv(index=False).encode(),
                       "historical-alerts.csv", "text/csv", key="history_export")

with st.container(border=True):
    st.subheader(tr("02 / Provoca un cambio sintético", "02 / Introduce a synthetic change"))
    controls = st.columns(3)
    kind = controls[0].radio("Cambio / Change", ["spike", "shift"], key="kind",
                                format_func=lambda value: {"spike": "Pico / Spike", "shift": "Cambio sostenido / Sustained shift"}[value])
    amplitude = controls[1].slider("Amplitud / Amplitude", -30.0, 30.0, 10.0, step=.5, key="amplitude")
    position = controls[2].slider("Posición / Position", 0, len(selected) - 1, min(48, len(selected) - 1), key="position")
    # Retain exactly 11 prior raw readings so the first displayed score has causal context.
    first = raw.index[raw.timestamp == selected.timestamp.iloc[0]][0]
    context = raw.iloc[first - 11:first + len(selected)].copy()
    result = perturb_window(context, saved, kind, amplitude, position + 11, baseline_threshold)
    result = result.assign(scenario_kind=kind, amplitude=amplitude, change_position=position,
                           selected_detector=detector, model_threshold=saved["threshold"],
                           baseline_threshold=baseline_threshold)
    original_alert = "original_alert" if detector == "isolation_forest" else "baseline_original_alert"
    scenario_alert = "scenario_alert" if detector == "isolation_forest" else "baseline_scenario_alert"
    chart = result[["timestamp", "original_value", "scenario_value"]].rename(
        columns={"original_value": "Original", "scenario_value": "Scenario"})
    line_chart(chart, ["Original", "Scenario"], tr("Temperatura", "Temperature"))
    alerts = st.columns(3)
    alerts[0].metric(tr("Alertas originales / ventana", "Original alerts / window"), int(result[original_alert].sum()))
    alerts[1].metric(tr("Alertas del escenario / ventana", "Scenario alerts / window"), int(result[scenario_alert].sum()))
    alerts[2].metric(tr("Alertas nuevas", "New alerts"), int((result[scenario_alert] & ~result[original_alert]).sum()))
    st.download_button("CSV / " + tr("Escenario", "Scenario"), result.to_csv(index=False).encode(),
                       "anomaly-scenario.csv", "text/csv", key="scenario_export")
    st.warning(tr("Datos modificados solo en memoria. Modelo y umbrales permanecen fijos. Las etiquetas históricas no describen el escenario: no se calcula precisión ni recall sobre datos sintéticos.",
                  "Data is modified only in memory. Model and thresholds remain fixed. Historical labels do not describe the scenario: precision and recall are not calculated on synthetic data."))

st.info(tr("Métricas históricas por punto dentro de ventanas etiquetadas; no es la puntuación oficial NAB. Una alerta requiere contexto y revisión, no equivale a una avería confirmada.",
           "Historical pointwise metrics inside labeled windows; not the official NAB score. An alert needs context and review; it does not confirm a failure."))
with st.expander(tr("Protocolo y resultados completos", "Protocol and full results")):
    st.json(report)
