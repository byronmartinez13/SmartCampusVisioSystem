import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app import settings, store
from app.main import app
from app.processor import Cancelled, inspect_video, process_video
from app.detector import YoloDetector


class StubDetector:
    metadata = {"model": "test-double", "seat_semantics": "chairs"}

    def __init__(self, counts=(1, 3, 2)):
        self.counts = iter(counts)

    def detect(self, frame, confidence):
        return [{"kind": "person", "class": "person", "confidence": .9, "xyxy": [1, 1, 30, 30]}
                for _ in range(next(self.counts))]


class ProcessorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.video = self.root / "test.mp4"
        writer = cv2.VideoWriter(str(self.video), cv2.VideoWriter_fourcc(*"mp4v"), 2, (64, 64))
        for _ in range(3):
            writer.write(np.zeros((64, 64, 3), np.uint8))
        writer.release()

    def process(self, detector, cancelled=lambda: False):
        return process_video(self.video, detector, .5, self.root / "preview.jpg", lambda _: None, cancelled)

    def test_peak_not_accumulated_people_and_preview(self):
        result = self.process(StubDetector())
        self.assertEqual(result["people_max"], 3)
        self.assertEqual(result["people_mean"], 2)
        self.assertEqual(result["peak_sample"]["frame"], 1)
        self.assertEqual(result["sampled_frames"], 3)
        self.assertTrue((self.root / "preview.jpg").is_file())

    def test_no_detections_is_valid_result(self):
        self.assertEqual(self.process(StubDetector((0, 0, 0)))["people_max"], 0)

    def test_cancellation_stops_processing(self):
        with self.assertRaises(Cancelled):
            self.process(StubDetector(), lambda: True)

    def test_invalid_file_and_duration_limit(self):
        invalid = self.root / "invalid.mp4"
        invalid.write_bytes(b"not a video")
        with self.assertRaises(ValueError):
            inspect_video(invalid)
        with patch.object(settings, "MAX_SECONDS", 1), self.assertRaises(ValueError):
            inspect_video(self.video)

    def test_service_authentication_upload_idempotency_and_cancel(self):
        with patch.object(settings, "DATA_DIR", self.root / "data"), patch.object(settings, "API_KEY", "test-key"):
            store.initialize()
            client = TestClient(app)  # No lifespan: worker deliberately excluded from deterministic API test.
            self.assertEqual(client.get("/v1/jobs/00000000-0000-0000-0000-000000000001").status_code, 401)
            headers = {"X-Vision-Key": "test-key"}
            job_id = "00000000-0000-0000-0000-000000000001"
            for _ in range(2):
                response = client.post("/v1/jobs", headers=headers, data={"job_id": job_id},
                                       files={"video": ("test.mp4", self.video.read_bytes(), "video/mp4")})
                self.assertEqual(response.status_code, 202, response.text)
            self.assertEqual(store.queue_size(), 1)
            self.assertEqual(client.post(f"/v1/jobs/{job_id}/cancel", headers=headers).status_code, 200)
            self.assertEqual(store.get(job_id)["status"], "cancelled")

    def test_restart_recovers_interrupted_job(self):
        with patch.object(settings, "DATA_DIR", self.root / "data"):
            store.initialize()
            store.insert("test", .5)
            self.assertEqual(store.claim_next(), "test")
            store.initialize()
            self.assertEqual(store.get("test")["status"], "queued")

    def test_monitor_reference_selects_tv_not_chair(self):
        weights = self.root / "test.pt"
        weights.write_bytes(b"test weights")
        model = SimpleNamespace(names={0: "person", 56: "chair", 62: "tv"})
        with patch.dict("sys.modules", {"ultralytics": SimpleNamespace(YOLO=lambda _: model)}), \
                patch.object(settings, "MODEL_PATH", weights), \
                patch.object(settings, "PERSON_CLASSES", ["person"]), \
                patch.object(settings, "SEAT_CLASSES", ["tv"]), \
                patch.object(settings, "SEAT_SEMANTICS", "monitors"):
            detector = YoloDetector()
            self.assertEqual(detector.class_ids, [0, 62])
            self.assertEqual(detector.metadata["seat_semantics"], "monitors")
            self.assertEqual(detector.metadata["seat_classes"], ["tv"])
