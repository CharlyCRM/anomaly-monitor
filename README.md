# Detectar lo inesperado / Anomaly Monitor

Proyecto de Carlos Ramírez Martín: un monitor de anomalías con features causales, calibración temporal, baseline estadístico, Isolation Forest, API y demo.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python monitor.py
pytest -q
streamlit run app.py --server.address 127.0.0.1
uvicorn api:app --host 127.0.0.1 --port 8002
```

## Protocolo

Serie `realKnownCause/ambient_temperature_system_failure.csv` de [Numenta Anomaly Benchmark](https://github.com/numenta/NAB). 35% inicial para ajustar el modelo, 15% siguiente para calibrar umbrales sin etiquetas y 50% final para test. Percentil 99 de scores de calibración, tanto para Isolation Forest como para el baseline de desviación estandarizada.

Se evalúan precisión, recall, F1 y falsos positivos por punto, junto con detección por ventana. **No se implementa ni se reclama la puntuación oficial NAB**. Las etiquetas son ventanas temporales y sus tamaños afectan a las métricas por punto. El informe expone si hay anomalías en los segmentos usados para ajuste y calibración; no se eliminan usando conocimiento de las etiquetas.

`artifacts/metrics.json` conserva protocolo, checksum y resultados medidos. `predictions.csv` permite reconstruir las visualizaciones. La diferencia estandarizada de medias muestra cambio de distribución, pero no demuestra su causa ni constituye una prueba estadística de drift.

## Aplicación interactiva

Abre http://localhost:8502/ (inglés: `/?lang=en`). Interfaz oscura ES/EN, selector de detector y ventana, temperatura con alertas superpuestas, scores frente al umbral y exportación CSV. La configuración limita el servicio a loopback y desactiva telemetría.

El escenario introduce un pico o cambio sostenido únicamente en memoria. Conserva once lecturas previas para construir features causales y utiliza el modelo, scaler y umbral guardados. El umbral del baseline se reproduce desde el segmento original de calibración sin usar etiquetas ni escenarios. No se vuelve a entrenar, no se cambian datos y no se calculan precisión/recall sintéticos con etiquetas históricas.

Cambiar de idioma conserva detector y controles. Si faltan artefactos, muestra instrucciones sin entrenar ni descargar. `PORTFOLIO_URL` configura el enlace de regreso; por defecto http://localhost:4322.

## API

`POST /score` acepta `{"values": [12 o más lecturas ordenadas]}` y devuelve score, umbral y alerta para la última lectura. No procesa lotes como si compartieran historia ni ofrece diagnósticos de averías.

## Datos y licencia

Descarga automática del repositorio NAB, publicado bajo AGPL-3.0; se conserva la atribución y los datos se mantienen fuera del repositorio propio. La licencia del código de este proyecto es MIT y no sustituye la licencia del dataset. No se importa código de NAB.
