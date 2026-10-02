"""Estilos y gráficos compartidos por las pantallas de la aplicación."""
import os
from html import escape
from pathlib import Path

import streamlit as st

CSS = """
<style>
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {background:#080c12;color:#edf2f7}
[data-testid="stSidebar"] {background:#101925;border-right:1px solid #263446}
.block-container {max-width:1280px;padding:2.5rem 2rem 4rem}
.hero {padding:1.5rem 0 2rem;border-bottom:1px solid #263446;margin-bottom:2rem}
.hero .eyebrow {color:#40d9dd;letter-spacing:.16em;font-size:.75rem;font-weight:700}
.hero h1 {font-size:clamp(2.7rem,6vw,5rem);line-height:1.02;letter-spacing:-.055em;max-width:900px;margin:1rem 0}
.hero .lead {color:#a8b7c7;max-width:780px;font-size:1.13rem;line-height:1.7}
.signature {color:#a8b7c7;font-size:.75rem;letter-spacing:.12em}
[data-testid="stMetric"] {background:#101925;border:1px solid #263446;border-radius:12px;padding:1.1rem}
[data-testid="stMetricValue"] {color:#40d9dd}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#263446!important}
.stButton button[kind="primary"] {background:#40d9dd;color:#080c12;border:0}
.stDownloadButton button, .stLinkButton a {border-color:#3c5667}
[data-testid="stAlert"] {border-radius:8px}
@media(max-width:600px){.block-container{padding:1.5rem 1rem 3rem}.hero h1{font-size:2.8rem}}
</style>
"""

def init(slug, title):
    st.set_page_config(page_title=f"{title} · Carlos Ramírez Martín", layout="wide",
                       initial_sidebar_state="auto")
    st.markdown(CSS, unsafe_allow_html=True)
    if "language" not in st.session_state:
        language = st.query_params.get("lang", "es")
        st.session_state.language = language if language in ("es", "en") else "es"
    with st.sidebar:
        st.markdown("### Carlos Ramírez Martín")
        st.caption("DATA SCIENCE / AI ENGINEERING")
        st.radio("Idioma / Language", ["es", "en"], key="language", horizontal=True,
                     format_func=lambda value: {"es": "Español", "en": "English"}[value])
        base = os.getenv("PORTFOLIO_URL", "http://localhost:4322").rstrip("/")
    st.query_params["lang"] = st.session_state.language
    st.link_button("← Portfolio", f"{base}/{st.session_state.language}/projects/{slug}/")
    return st.session_state.language

def tr(es, en):
    return en if st.session_state.get("language") == "en" else es

def hero(number, title, lead):
    st.markdown(f'<div class="signature">CARLOS RAMÍREZ MARTÍN / PYTHON + AI SYSTEMS</div>'
                f'<div class="hero"><div class="eyebrow">{escape(number)}</div>'
                f'<h1>{escape(title)}</h1><p class="lead">{escape(lead)}</p></div>',
                unsafe_allow_html=True)

def require_files(root, paths, command):
    missing = [str(path) for path in paths if not (Path(root) / path).exists()]
    if missing:
        st.warning(tr("Faltan artefactos locales. Prepara el proyecto antes de explorar.",
                      "Local artifacts are missing. Prepare the project before exploring."))
        st.code(command)
        st.caption(", ".join(missing))
        st.stop()

def line_chart(frame, columns, y_title, height=340):
    data = frame.reset_index(drop=True).melt(id_vars="timestamp", value_vars=columns,
                                            var_name="Series", value_name="Value")
    st.vega_lite_chart(data, {
        "background": "#101925", "height": height,
        "mark": {"type": "line", "strokeWidth": 2},
        "encoding": {
            "x": {"field": "timestamp", "type": "temporal", "title": None},
            "y": {"field": "Value", "type": "quantitative", "title": y_title, "scale": {"zero": False}},
            "color": {"field": "Series", "type": "nominal", "scale": {"domain": columns, "range": ["#40d9dd", "#b8f277", "#8295ac"]},
                      "legend": {"orient": "top", "title": None}},
            "tooltip": [{"field": "timestamp", "type": "temporal"}, {"field": "Series"}, {"field": "Value", "format": ".2f"}]
        },
        "config": {"axis": {"labelColor": "#a8b7c7", "titleColor": "#a8b7c7", "gridColor": "#263446"},
                   "legend": {"labelColor": "#dce6f0"}, "view": {"stroke": None}}
    }, width="stretch")

def alert_chart(frame):
    st.vega_lite_chart(frame, {
        "background": "#101925", "height": 340,
        "encoding": {"x": {"field": "timestamp", "type": "temporal", "title": None},
                     "y": {"field": "value", "type": "quantitative", "title": tr("Temperatura", "Temperature"),
                           "scale": {"zero": False}}},
        "layer": [
            {"mark": {"type": "line", "color": "#40d9dd", "strokeWidth": 2}},
            {"transform": [{"filter": "datum.alert === true"}],
             "mark": {"type": "point", "color": "#ffa66b", "filled": True, "size": 70},
             "encoding": {"tooltip": [{"field": "timestamp", "type": "temporal"}, {"field": "value"}, {"field": "score"}]}}
        ],
        "config": {"axis": {"labelColor": "#a8b7c7", "titleColor": "#a8b7c7", "gridColor": "#263446"}, "view": {"stroke": None}}
    }, width="stretch")
