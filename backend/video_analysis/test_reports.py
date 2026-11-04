from io import BytesIO
from pypdf import PdfReader
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from campus.models import Classroom
from .models import VideoJob


class ReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='reports@test.edu', name='Consulta')
        self.room = Classroom.objects.create(name='Laboratorio & <Norte>', capacity=40, validated_capacity=40)
        self.job = VideoJob.objects.create(classroom=self.room, creator=self.user, activity='practice',
            video='private.mp4', original_name='práctica.mp4', capacity_snapshot=20, status='completed',
            result={'people_max': 22, 'people_mean': 18, 'seats_max': 30, 'sampled_frames': 10,
                    'detector': {'seat_semantics': 'monitors', 'model': 'YOLO', 'sha256': 'a' * 64}})
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def text(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('no-store', response['Cache-Control'])
        return '\n'.join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)

    def test_individual_snapshot_semantics_and_permissions(self):
        url = f'/api/video-analyses/{self.job.pk}/report/'
        text = self.text(self.client.get(url))
        self.assertIn('110.0 %', text)
        self.assertIn('Monitores (máximo detectado)', text)
        self.assertIn('Laboratorio & <Norte>', text)
        self.assertNotIn('private.mp4', text)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_pending_rejected_and_missing_capacity(self):
        self.job.status = 'queued'
        self.job.save()
        url = f'/api/video-analyses/{self.job.pk}/report/'
        self.assertEqual(self.client.get(url).status_code, 400)
        self.job.status = 'completed'
        self.job.capacity_snapshot = None
        self.job.save()
        self.assertIn('No disponible', self.text(self.client.get(url)))

    def test_consolidated_filters_empty_invalid_and_all_pages(self):
        url = '/api/analysis-history/report/'
        self.assertIn(str(self.job.pk), ''.join(self.text(self.client.get(url + '?page=3')).split()))
        self.assertIn('No hay análisis', self.text(self.client.get(url + '?activity=exam')))
        self.assertEqual(self.client.get(url + '?date_from=2026-11-02&date_to=2026-01-01').status_code, 400)
        self.assertIn('No hay análisis', self.text(self.client.get(url + '?status=queued')))
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_consolidated_limit_requires_narrower_filters(self):
        VideoJob.objects.bulk_create([VideoJob(classroom=self.room, creator=self.user, activity='class',
            video='x.mp4', original_name='x.mp4', status='completed', result={'people_max': 1}) for _ in range(500)])
        self.assertEqual(self.client.get('/api/analysis-history/report/').status_code, 400)
