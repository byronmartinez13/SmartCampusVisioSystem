import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import settings, store
from app.main import app


class DeletionTests(unittest.TestCase):
    def test_terminal_only_authenticated_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(settings, 'DATA_DIR', Path(temp)), patch.object(settings, 'API_KEY', 'delete-test'):
            store.initialize()
            ident = str(uuid4())
            store.insert(ident, .5)
            folder = Path(temp) / ident
            folder.mkdir()
            (folder / 'input.video').write_bytes(b'video')
            (folder / 'preview.jpg').write_bytes(b'preview')
            client = TestClient(app)
            url = f'/v1/jobs/{ident}'
            headers = {'X-Vision-Key': 'delete-test'}
            self.assertEqual(client.delete(url).status_code, 401)
            self.assertEqual(client.delete(url, headers=headers).status_code, 409)
            self.assertTrue(folder.exists())
            store.update(ident, status='completed')
            self.assertEqual(client.delete(url, headers=headers).status_code, 204)
            self.assertIsNone(store.get(ident))
            self.assertFalse(folder.exists())
            self.assertEqual(client.delete(url, headers=headers).status_code, 204)
            self.assertEqual(client.delete('/v1/jobs/not-a-uuid', headers=headers).status_code, 422)
