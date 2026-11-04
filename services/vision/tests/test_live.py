import io
import unittest
from unittest.mock import patch
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app import settings
from app.main import app


class LiveFrameTests(unittest.TestCase):
    def test_authentication_validation_and_detector(self):
        client = TestClient(app)
        image = cv2.imencode('.jpg', np.zeros((100, 120, 3), dtype=np.uint8))[1].tobytes()
        with patch.object(settings, 'API_KEY', 'test-live'):
            self.assertEqual(client.post('/v1/frame', files={'image': ('x.jpg', image)}).status_code, 401)
            headers = {'X-Vision-Key': 'test-live'}
            self.assertEqual(client.post('/v1/frame', headers=headers, files={'image': ('x.jpg', b'bad')}).status_code, 400)
            with patch('app.main.live_detector') as detector:
                detector.metadata = {'model': 'explicit-test'}
                detector.detect.return_value = [{'kind': 'person'}, {'kind': 'seat'}]
                response = client.post('/v1/frame', headers=headers, files={'image': ('x.jpg', image)})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['people'], 1)
                self.assertEqual(response.json()['seats'], 1)
                self.assertEqual(response.json()['width'], 120)
