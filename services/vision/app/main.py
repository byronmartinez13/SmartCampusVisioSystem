import hmac
import logging
import os
import threading
import cv2
import numpy as np
from contextlib import asynccontextmanager
from uuid import UUID
from fastapi import FastAPI, File, Form, Header, HTTPException, Security, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from . import settings, store
from .detector import YoloDetector
from .processor import Cancelled, inspect_video, process_video

logger = logging.getLogger(__name__)
key_header = APIKeyHeader(name="X-Vision-Key", auto_error=False)
upload_lock = threading.Lock()
stop = threading.Event()
inference_lock = threading.Lock()
live_detector = None


def authenticate(key=Security(key_header)):
    if not settings.API_KEY or not key or not hmac.compare_digest(key, settings.API_KEY):
        raise HTTPException(401, "Credenciales del servicio no válidas.")


def run_worker():
    detector = None
    while not stop.is_set():
        job_id = store.claim_next()
        if job_id is None:
            stop.wait(.5)
            continue
        job = store.get(job_id)
        directory = settings.DATA_DIR / job_id
        try:
            if detector is None:
                detector = YoloDetector()
            result = process_video(
                directory / "input.video", detector, job["confidence"], directory / "preview.jpg",
                progress=lambda value: store.update(job_id, progress=value),
                cancelled=lambda: stop.is_set() or bool(store.get(job_id)["cancelled"]),
            )
            if store.get(job_id)["cancelled"]:
                raise Cancelled()
            store.update(job_id, status="completed", progress=100, result=result)
        except Cancelled:
            if not stop.is_set():
                store.update(job_id, status="cancelled")
            # An interrupted process remains processing, to be resumed after restart.
        except ValueError as exc:
            store.update(job_id, status="failed", error=str(exc))
        except Exception:
            logger.exception("Fallo interno del detector para %s", job_id)
            store.update(job_id, status="failed", error="No se pudo procesar el video con el detector.")


@asynccontextmanager
async def lifespan(app):
    if not settings.API_KEY:
        raise RuntimeError("Define VISION_API_KEY antes de iniciar el microservicio.")
    store.initialize()
    stop.clear()
    thread = threading.Thread(target=run_worker, daemon=True)
    thread.start()
    yield
    stop.set()
    thread.join(timeout=5)


app = FastAPI(title="Smart Campus Vision · Visión", version="1.0.0", lifespan=lifespan)


@app.post('/v1/frame', dependencies=[Security(authenticate)])
def analyze_frame(image: UploadFile = File(...), confidence: float = Form(.5, ge=.1, le=.95)):
    global live_detector
    content = image.file.read(2 * 1024 * 1024 + 1)
    image.file.close()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(413, 'La imagen supera 2 MB.')
    # Inspect dimensions before OpenCV allocates the decoded image.
    from PIL import Image
    from io import BytesIO
    try:
        with Image.open(BytesIO(content)) as probe:
            if probe.format != 'JPEG' or max(probe.size) > 1920 or min(probe.size) < 1:
                raise ValueError()
            probe.verify()
    except Exception:
        raise HTTPException(400, 'Se requiere un JPEG válido de hasta 1920 píxeles por lado.')
    frame = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, 'No se pudo leer la imagen.')
    if not inference_lock.acquire(blocking=False):
        raise HTTPException(429, 'El detector está ocupado. Intenta de nuevo.')
    try:
        if live_detector is None:
            live_detector = YoloDetector()
        boxes = live_detector.detect(frame, confidence)
        return {'boxes': boxes, 'people': sum(b['kind'] == 'person' for b in boxes),
                'seats': sum(b['kind'] == 'seat' for b in boxes), 'detector': live_detector.metadata,
                'width': frame.shape[1], 'height': frame.shape[0]}
    finally:
        inference_lock.release()


@app.get("/health")
def health():
    return {"status": "ok", "model_available": settings.MODEL_PATH.is_file()}


@app.post("/v1/jobs", status_code=202, dependencies=[Security(authenticate)])
def create_job(job_id: UUID = Form(...), confidence: float = Form(.5, ge=.1, le=.95),
               video: UploadFile = File(...)):
    job_id = str(job_id)
    with upload_lock:
        existing = store.get(job_id)
        if existing:
            return {"id": job_id, "status": existing["status"]}
        if store.queue_size() >= 10:
            raise HTTPException(429, "La cola de análisis está llena. Inténtalo más tarde.")
        directory = settings.DATA_DIR / job_id
        directory.mkdir(exist_ok=True)
        destination = directory / "input.video"
        size = 0
        try:
            with destination.open("wb") as output:
                while chunk := video.file.read(1024 * 1024):
                    size += len(chunk)
                    if size > settings.MAX_BYTES:
                        raise HTTPException(413, "El video supera 250 MB.")
                    output.write(chunk)
            if size == 0:
                raise HTTPException(400, "El archivo está vacío.")
            inspect_video(destination)
            store.insert(job_id, confidence)
        except ValueError as exc:
            destination.unlink(missing_ok=True)
            raise HTTPException(400, str(exc)) from exc
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            video.file.close()
    return {"id": job_id, "status": "queued"}


@app.get("/v1/jobs/{job_id}", dependencies=[Security(authenticate)])
def get_job(job_id: UUID):
    job = store.get(str(job_id))
    if not job:
        raise HTTPException(404, "Análisis no encontrado.")
    return job


@app.delete('/v1/jobs/{job_id}', status_code=204, dependencies=[Security(authenticate)])
def delete_job(job_id: UUID):
    from fastapi import Response
    with upload_lock:
        try:
            store.delete(str(job_id))
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
    return Response(status_code=204)


@app.post("/v1/jobs/{job_id}/cancel", dependencies=[Security(authenticate)])
def cancel_job(job_id: UUID):
    job = store.get(str(job_id))
    if not job:
        raise HTTPException(404, "Análisis no encontrado.")
    if job["status"] not in ("completed", "failed", "cancelled"):
        store.update(str(job_id), cancelled=1, status="cancelled" if job["status"] == "queued" else job["status"])
    return {"id": str(job_id)}


@app.get("/v1/jobs/{job_id}/preview", dependencies=[Security(authenticate)])
def preview(job_id: UUID):
    path = settings.DATA_DIR / str(job_id) / "preview.jpg"
    if not store.get(str(job_id)) or not path.is_file():
        raise HTTPException(404, "Todavía no hay una imagen disponible.")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "no-store"})
