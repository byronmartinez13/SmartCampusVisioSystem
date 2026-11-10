from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from campus.models import Classroom, Alert
from .models import VideoJob


class LiveTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='live@test.edu', name='Admin', role='admin')
        self.other = User.objects.create_user(email='other@test.edu', name='Other', role='admin')
        self.viewer = User.objects.create_user(email='view@test.edu', name='Viewer')
        self.room = Classroom.objects.create(name='Live room', capacity=30, validated_capacity=2)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def start(self):
        response = self.client.post('/api/live-sessions/', {'classroom': self.room.pk}, format='json')
        self.assertEqual(response.status_code, 201)
        return response.data['id']

    def frame(self, ident):
        return self.client.post(f'/api/live-sessions/{ident}/frame/', {'image': SimpleUploadedFile('frame.jpg', b'jpeg')}, format='multipart')

    @patch('video_analysis.live.VisionClient')
    def test_counts_are_server_results_snapshot_stop_save_and_report(self, client):
        client.return_value.frame.return_value = {'people': 3, 'seats': 4, 'boxes': [], 'width': 640, 'height': 480,
                                                  'detector': {'model': 'explicit-test', 'seat_semantics': 'monitors'}}
        ident = self.start()
        self.room.validated_capacity = 20; self.room.save()
        self.assertEqual(self.frame(ident).status_code, 200)
        self.assertEqual(self.frame(ident).data['samples'], 2)
        stop = f'/api/live-sessions/{ident}/stop/'
        self.assertEqual(self.client.post(stop).data['status'], 'completed')
        self.assertEqual(self.client.post(stop).data['status'], 'completed')
        self.assertEqual(self.frame(ident).status_code, 400)
        job = VideoJob.objects.get(pk=ident)
        self.assertFalse(job.video)
        from .services import synchronize
        from unittest.mock import Mock
        worker_client = Mock()
        synchronize(job, worker_client)
        worker_client.status.assert_not_called()
        self.assertEqual(job.capacity_snapshot, 2)
        for _ in range(2):
            self.assertEqual(self.client.post(f'/api/video-analyses/{ident}/save-result/').status_code, 200)
        self.assertEqual(Alert.objects.count(), 1)
        self.assertEqual(self.client.get(f'/api/video-analyses/{ident}/report/').status_code, 200)

    def test_roles_owner_empty_stop_and_retry(self):
        ident = self.start()
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(f'/api/live-sessions/{ident}/stop/').status_code, 404)
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.post('/api/live-sessions/', {'classroom': self.room.pk}).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(f'/api/live-sessions/{ident}/stop/').data['status'], 'cancelled')
        self.assertEqual(self.client.post(f'/api/video-analyses/{ident}/retry/').status_code, 400)

    def test_expired_and_missing_frame(self):
        from datetime import timedelta
        from django.utils import timezone
        ident = self.start()
        self.assertEqual(self.client.post(f'/api/live-sessions/{ident}/frame/').status_code, 400)
        VideoJob.objects.filter(pk=ident).update(created_at=timezone.now() - timedelta(minutes=11))
        self.assertEqual(self.frame(ident).status_code, 400)

    def test_monitor_signaling_is_private_validated_and_stops_with_session(self):
        from uuid import uuid4
        ident = self.start()
        url = f'/api/live-sessions/{ident}/monitor/'
        viewer = str(uuid4())
        offer = {'kind': 'offer', 'viewer': viewer, 'sdp': 'v=0\r\ns=test-offer\r\n'}
        self.assertEqual(self.client.post(url, offer, format='json').status_code, 200)
        self.assertEqual(self.client.get(url).data['offer']['viewer'], viewer)
        self.assertEqual(self.client.get(url).data['offer']['sdp'], offer['sdp'])
        wrong = {'kind': 'answer', 'viewer': str(uuid4()), 'sdp': 'test-answer'}
        self.assertEqual(self.client.post(url, wrong, format='json').status_code, 409)
        wrong['viewer'] = viewer
        self.assertEqual(self.client.post(url, wrong, format='json').status_code, 200)
        self.assertEqual(self.client.get(url).data['answer']['sdp'], 'test-answer')
        self.assertEqual(self.client.get(url)['Cache-Control'], 'no-store')
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, offer, format='json').status_code, 404)
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_authenticate(self.admin)
        offer['sdp'] = 'x' * 65537
        self.assertEqual(self.client.post(url, offer, format='json').status_code, 400)
        self.client.post(f'/api/live-sessions/{ident}/stop/')
        self.assertIsNone(self.client.get(url).data['offer'])
        offer['sdp'] = 'offer'
        self.assertEqual(self.client.post(url, offer, format='json').status_code, 400)

    @patch('video_analysis.live.VisionClient')
    def test_in_flight_sample_cannot_reopen_stopped_session(self, client):
        ident = self.start()
        def inference(*args):
            self.client.post(f'/api/live-sessions/{ident}/stop/')
            return {'people': 1, 'seats': 0, 'boxes': [], 'width': 100, 'height': 100, 'detector': {}}
        client.return_value.frame.side_effect = inference
        self.assertEqual(self.frame(ident).status_code, 409)
        self.assertEqual(VideoJob.objects.get(pk=ident).status, 'cancelled')
