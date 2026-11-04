import hashlib
from typing import Protocol
from . import settings


class Detector(Protocol):
    metadata: dict

    def detect(self, frame, confidence: float) -> list[dict]: ...


class YoloDetector:
    def __init__(self):
        if not settings.MODEL_PATH.is_file():
            raise ValueError("No se encontraron los pesos del detector. Configura el modelo de visión.")
        from ultralytics import YOLO
        self.model = YOLO(str(settings.MODEL_PATH))
        names = self.model.names
        people = {idx for idx, name in names.items() if name in settings.PERSON_CLASSES}
        seats = {idx for idx, name in names.items() if name in settings.SEAT_CLASSES}
        if not people or not seats or people & seats:
            raise ValueError("Las clases de personas y asientos no coinciden con el modelo configurado.")
        if settings.SEAT_SEMANTICS not in ("chairs", "workstations", "monitors"):
            raise ValueError("La semántica de asientos del modelo no es válida.")
        self.people_ids = people
        self.seat_ids = seats
        self.class_ids = sorted(people | seats)
        self.metadata = {
            "model": settings.MODEL_PATH.name,
            "sha256": hashlib.sha256(settings.MODEL_PATH.read_bytes()).hexdigest(),
            "person_classes": settings.PERSON_CLASSES,
            "seat_classes": settings.SEAT_CLASSES,
            "seat_semantics": settings.SEAT_SEMANTICS,
            "device": "cpu",
            "image_size": 640,
        }

    def detect(self, frame, confidence):
        result = self.model.predict(frame, conf=confidence, imgsz=640, device="cpu",
                                    classes=self.class_ids, max_det=300, verbose=False)[0]
        boxes = []
        for item in result.boxes:
            class_id = int(item.cls.item())
            boxes.append({
                "kind": "person" if class_id in self.people_ids else "seat",
                "class": self.model.names[class_id],
                "confidence": round(float(item.conf.item()), 4),
                "xyxy": [round(float(x), 1) for x in item.xyxy[0].tolist()],
            })
        return boxes
