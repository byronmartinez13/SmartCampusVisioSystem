# Microservicio de visión

FastAPI + Ultralytics YOLO11n + OpenCV, con cola SQLite persistente y un trabajador de inferencia CPU. Django se comunica por HTTP autenticado con `X-Vision-Key`; el navegador nunca recibe esa clave.

Desde la raíz del proyecto:

```powershell
python -m venv services/vision/.venv
.\services\vision\.venv\Scripts\python.exe -m pip install -r services/vision/requirements.lock.txt
New-Item -ItemType Directory -Force services/vision/models
Invoke-WebRequest https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt -OutFile services/vision/models/yolo11n.pt
.\services\vision\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir services/vision --host 127.0.0.1 --port 8002
```

Definir `VISION_API_KEY` en el `.env` de la raíz. No usar el valor de ejemplo. Django usa la misma clave. Las dependencias quedaron fijadas con Python 3.13 en Windows; verificar de nuevo en el entorno Linux de despliegue.

- `GET /health`: disponibilidad del proceso y presencia del archivo de pesos.
- `POST /v1/jobs`: multipart `job_id` UUID, `confidence`, `video`. Idempotente por UUID.
- `GET /v1/jobs/{id}`: estado, progreso y resultado.
- `POST /v1/jobs/{id}/cancel`: solicita cancelación.
- `GET /v1/jobs/{id}/preview`: JPEG anotado del fotograma con mayor conteo.

Todo salvo `/health` requiere la clave interna. Ejecutar **una sola instancia y un solo worker de Uvicorn** para esta cola local. No exponer el puerto directamente en Internet.

Datos en `services/vision/data/`; pesos en `services/vision/models/`. Ambos se excluyen de Git. El servicio no descarga pesos durante una solicitud. Un proceso interrumpido se reencola al reiniciar.

Cambiar `VISION_MODEL_PATH`, `VISION_PERSON_CLASSES`, `VISION_SEAT_CLASSES` y `VISION_SEAT_SEMANTICS` al incorporar el modelo entrenado. Las clases deben existir en el modelo y ser disjuntas. La configuración actual usa `VISION_SEAT_CLASSES=tv` y `VISION_SEAT_SEMANTICS=monitors`: referencia visual de pantallas para laboratorios. La clase `tv` del modelo general también incluye detecciones de televisores; no equivale a puestos utilizables. Usar `workstations` solo para un modelo que realmente detecte puestos.

Por compatibilidad del contrato JSON, los campos `seats_max`, `samples[].seats` y las cajas `kind=seat` siguen almacenando el conteo de objetos de referencia. Su significado lo determina siempre `detector.seat_semantics`: `chairs`, `monitors` o `workstations`. El frontend lee los metadatos guardados de cada resultado y nunca cambia las sillas de un análisis histórico por monitores.

Pruebas:

```powershell
cd services/vision
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Las pruebas deterministas emplean un detector de prueba explícito. `validate_samples.py` llama al servicio HTTP con el YOLO real y los cuatro videos del inventario local; genera `docs/vision-validation.json`, sin afirmar precisión.
