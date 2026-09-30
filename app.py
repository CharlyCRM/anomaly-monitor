import json

import pandas as pd
import streamlit as st
from monitor import ROOT

st.set_page_config(page_title="Anomaly Monitor", layout="wide")
st.title("Detectar lo inesperado")
st.caption("Temperatura de un sistema · NAB · Carlos Ramírez Martín")
if not (ROOT / "artifacts/metrics.json").exists():
    st.info("Ejecuta python monitor.py.")
    st.stop()
report = json.loads((ROOT / "artifacts/metrics.json").read_text())
metrics = report["isolation_forest"]
cols = st.columns(3)
cols[0].metric("Precision por punto", f"{metrics['precision']:.3f}")
cols[1].metric("Recall por punto", f"{metrics['recall']:.3f}")
cols[2].metric("Falsos positivos", metrics["false_positives"])
frame = pd.read_csv(ROOT / "artifacts/predictions.csv")
offset = st.slider("Inicio de la ventana de test", 0, max(0, len(frame) - 288), 0)
window = frame.iloc[offset : offset + 288].set_index("timestamp")
st.line_chart(window[["value"]])
st.line_chart(window[["score"]])
st.dataframe(window[window.alert.astype(bool)], use_container_width=True)
st.warning(
    "Métricas por punto dentro de ventanas etiquetadas. No es la puntuación oficial de NAB. Las alertas requieren contexto y revisión."
)
st.json(report)
