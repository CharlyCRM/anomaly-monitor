# Detectar lo inesperado

Una temperatura puede parecer normal por sí sola y resultar extraña al compararla con las lecturas anteriores. En este proyecto exploro cómo detectar esos cambios en una serie de sensores, comparando Isolation Forest con una referencia estadística más sencilla.

La aplicación muestra las lecturas, las alertas y la puntuación de cada detector. También permite introducir un pico o un cambio sostenido para comprobar qué detecta cada método y qué puede pasar desapercibido.

[Abrir la aplicación](https://anomaly-monitor-production.up.railway.app) · [Ver el proyecto en mi portfolio](https://carlos-ramirez-martin.up.railway.app/es/projects/anomaly-monitor/)

## Qué puedes explorar

- Recorrer la temperatura y ver dónde aparecen alertas.
- Comparar las puntuaciones de los detectores con su umbral de alerta.
- Añadir un pico puntual o un cambio sostenido en una copia de la ventana seleccionada.
- Descargar el escenario en CSV para revisar las diferencias con la serie original.

Los escenarios solo existen en memoria: no sobrescriben los datos ni entrenan de nuevo el modelo. Cambiar de idioma conserva los controles. La demo está en español e inglés y se suspende cuando no se utiliza; la primera apertura puede tardar. La API se prueba por separado en local, no está publicada junto a la demo.

## Cómo se calculan las alertas

Trabajo con `realKnownCause/ambient_temperature_system_failure.csv` de Numenta Anomaly Benchmark. Para cada lectura calculo el valor actual, la media y desviación de las últimas doce lecturas y la diferencia respecto a la anterior. Ninguna de estas variables utiliza lecturas futuras.

Reservo el primer 35 % para ajustar el modelo y el escalado, el siguiente 15 % para fijar los umbrales y el 50 % final para evaluar. El umbral es el percentil 99 de las puntuaciones del bloque de calibración, tanto para Isolation Forest como para la referencia basada en la distancia a la media. Las etiquetas no intervienen en ese ajuste.

[artifacts/metrics.json](artifacts/metrics.json) recoge precisión, recall, F1, falsos positivos y detección dentro de las ventanas etiquetadas. Incluye el checksum de la serie y cuántas lecturas etiquetadas como anomalía hay en ajuste y calibración. No las retiro después de conocer las etiquetas.

## Cómo interpretar los resultados

Las etiquetas de NAB marcan intervalos, no únicamente el instante exacto de una avería. Su tamaño influye en las métricas por lectura. Este proyecto no implementa la puntuación oficial de NAB ni pretende sustituirla.

En los escenarios mantengo el modelo, el escalado y los umbrales originales. Conservo once lecturas anteriores a la ventana visible para calcular sus primeras puntuaciones. No uso las etiquetas históricas para atribuir precisión o recall a las alteraciones inventadas.

Una alerta señala una lectura poco habitual, no un diagnóstico. El indicador de cambio de distribución es descriptivo: no demuestra una causa ni constituye una prueba estadística de drift. Estudiar una sola serie tampoco asegura que el detector funcionará igual con otros sensores.

## Ejecutarlo en local

Necesitas Python 3.11. Desde la carpeta del repositorio:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python monitor.py
pytest -q
streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

Abre http://localhost:8502/; añade `/?lang=en` para entrar en inglés.

`monitor.py` descarga la serie y las etiquetas, y genera el modelo, las predicciones y el informe en `artifacts/`. Si faltan esos archivos, la aplicación muestra instrucciones en lugar de descargarlos o entrenar automáticamente. Los datos y el modelo generado quedan fuera de Git.

Para probar la API, abre otro terminal con el mismo entorno activado:

```sh
uvicorn api:app --host 127.0.0.1 --port 8002
```

La documentación está en http://127.0.0.1:8002/docs. `POST /score` recibe `values`, una lista de entre 12 y 1.000 lecturas ordenadas, y devuelve la puntuación, el umbral y la alerta de la última. Las lecturas anteriores aportan contexto, no se interpretan como ejemplos independientes. `GET /health` indica si el modelo está disponible.

La configuración local limita Streamlit a tu equipo y desactiva su telemetría. `PORTFOLIO_URL` cambia el enlace de regreso; por defecto usa `http://localhost:4322`.

## Datos y licencia

Los datos y etiquetas se descargan de [Numenta Anomaly Benchmark](https://github.com/numenta/NAB), publicado bajo AGPL-3.0. No importo código de NAB. El código propio tiene licencia MIT, que no sustituye las condiciones del dataset.

Carlos Ramírez Martín
