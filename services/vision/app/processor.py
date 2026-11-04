import math
import os
import time
from pathlib import Path
import cv2
from . import settings


class Cancelled(Exception):
    pass


def inspect_video(path):
    cap = cv2.VideoCapture(str(path))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width, height = int(cap.get(3)), int(cap.get(4))
        if not cap.isOpened() or not math.isfinite(fps) or fps <= 0 or count <= 0:
            raise ValueError("El archivo no contiene un video que se pueda decodificar.")
        if count / fps > settings.MAX_SECONDS:
            raise ValueError("El video supera el límite de 10 minutos.")
        if width <= 0 or height <= 0 or width * height > 4096 * 4096:
            raise ValueError("La resolución del video no está admitida.")
        ok, frame = cap.read()
        if not ok or frame is None:
            raise ValueError("No se pudo leer el primer fotograma del video.")
        return {"fps": fps, "frame_count": count, "width": width, "height": height,
                "duration_seconds": round(count / fps, 3)}
    finally:
        cap.release()


def write_preview(frame, boxes, destination):
    image = frame.copy()
    for box in boxes:
        x1, y1, x2, y2 = (int(v) for v in box["xyxy"])
        color = (245, 127, 56) if box["kind"] == "person" else (165, 181, 18)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        label = f'{box["class"]} {box["confidence"]:.0%}'
        cv2.putText(image, label, (x1, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, .5, color, 2)
    height, width = image.shape[:2]
    if width > 1280:
        image = cv2.resize(image, (1280, round(height * 1280 / width)))
    temporary = Path(destination).with_name("preview-temp.jpg")
    if not cv2.imwrite(str(temporary), image):
        raise ValueError("No se pudo generar la imagen del análisis.")
    os.replace(temporary, destination)


def process_video(path, detector, confidence, preview_path, progress, cancelled):
    metadata = inspect_video(path)
    stride = max(1, round(metadata["fps"] / settings.SAMPLE_FPS))
    cap = cv2.VideoCapture(str(path))
    samples = []
    frame_index = 0
    peak_people = -1
    started = time.monotonic()
    try:
        while True:
            if cancelled():
                raise Cancelled()
            ok, frame = cap.read()
            if not ok:
                break
            if frame_index % stride == 0:
                boxes = detector.detect(frame, confidence)
                people = sum(box["kind"] == "person" for box in boxes)
                seats = sum(box["kind"] == "seat" for box in boxes)
                samples.append({"frame": frame_index, "seconds": round(frame_index / metadata["fps"], 3),
                                "people": people, "seats": seats})
                if people > peak_people:
                    peak_people = people
                    peak_sample = {**samples[-1], "boxes": boxes}
                    write_preview(frame, boxes, preview_path)
                progress(min(99, round((frame_index + 1) / metadata["frame_count"] * 100)))
            frame_index += 1
        if not samples:
            raise ValueError("No se obtuvieron fotogramas para analizar.")
        if frame_index < metadata["frame_count"] - 2:
            raise ValueError("El video terminó antes de lo indicado: puede estar dañado o truncado.")
    finally:
        cap.release()
    return {
        "schema_version": 1, "video": metadata, "detector": detector.metadata,
        "confidence": confidence, "sample_stride": stride, "sampled_frames": len(samples),
        "people_max": max(s["people"] for s in samples),
        "people_mean": round(sum(s["people"] for s in samples) / len(samples), 2),
        "seats_max": max(s["seats"] for s in samples),
        "peak_sample": peak_sample, "samples": samples,
        "processing_seconds": round(time.monotonic() - started, 2),
    }
