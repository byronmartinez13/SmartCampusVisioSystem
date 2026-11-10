from pathlib import Path
from unittest.mock import patch
import httpx
from django.test import TestCase
from campus.models import Analysis, Alert, AlertEvent, AdministrativeEvent
from . import tests as video_tests


class DeletionTests(TestCase):
    setUp = video_tests.VideoAnalysisTests.setUp
    upload = video_tests.VideoAnalysisTests.upload
    job = video_tests.VideoAnalysisTests.job
    @patch('video_analysis.client.VisionClient.delete')
    def test_delete_removes_upload_summary_alerts_and_reports(self, remote_delete):
        job = self.job()
        upload = Path(job.video.path)
        job.status = 'completed'
        job.result = {'people_max': 25}
        summary = Analysis.objects.create(classroom=self.room, people=25, capacity=20)
        job.saved_analysis = summary
        job.save()
        alert = Alert.objects.create(analysis=summary)
        AlertEvent.objects.create(alert=alert, actor=self.admin, previous_status='new', status='review')
        response = self.client.delete(f'/api/video-analyses/{job.pk}/')
        self.assertEqual(response.status_code, 204)
        remote_delete.assert_called_once()
        self.assertFalse(upload.exists())
        self.assertFalse(Analysis.objects.filter(pk=summary.pk).exists())
        self.assertFalse(Alert.objects.filter(pk=alert.pk).exists())
        self.assertEqual(AlertEvent.objects.count(), 0)
        self.assertTrue(AdministrativeEvent.objects.filter(action='analysis.deleted', target=str(job.pk)).exists())
        self.assertEqual(self.client.get(f'/api/video-analyses/{job.pk}/').status_code, 404)
        self.assertEqual(self.client.get('/api/analysis-history/').data['count'], 0)
        self.assertEqual(self.client.get('/api/dashboard/').data['analyzed_classrooms'], 0)

    @patch('video_analysis.client.VisionClient.delete')
    def test_active_and_unauthorized_deletion_rejected(self, remote_delete):
        job = self.job()
        url = f'/api/video-analyses/{job.pk}/'
        self.assertEqual(self.client.delete(url).status_code, 400)
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.assertTrue(Path(job.video.path).exists())
        remote_delete.assert_not_called()

    @patch('video_analysis.client.VisionClient.delete', side_effect=httpx.ConnectError('unavailable'))
    def test_remote_failure_retains_record_and_local_file(self, remote_delete):
        job = self.job()
        job.status = 'failed'; job.save()
        self.assertEqual(self.client.delete(f'/api/video-analyses/{job.pk}/').status_code, 500)
        job.refresh_from_db()
        self.assertTrue(Path(job.video.path).exists())

    @patch('video_analysis.client.VisionClient.delete')
    def test_camera_delete_does_not_contact_video_service(self, remote_delete):
        response = self.client.post('/api/live-sessions/', {'classroom': self.room.pk}, format='json')
        ident = response.data['id']
        self.client.post(f'/api/live-sessions/{ident}/stop/')
        self.assertEqual(self.client.delete(f'/api/video-analyses/{ident}/').status_code, 204)
        remote_delete.assert_not_called()
