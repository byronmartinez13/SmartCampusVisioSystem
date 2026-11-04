from datetime import timedelta
from unittest.mock import Mock, patch
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import User
from video_analysis.models import VideoJob
from video_analysis.services import synchronize, save_summary
from .models import (Classroom, ClassroomAvailability, Teacher, Subject, Course, CourseMeeting,
                     AssignmentRule, SystemSettings, AdministrativeEvent, Alert)


class OperationsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='ops@test.edu', name='Admin', role='admin')
        self.viewer = User.objects.create_user(email='ops-view@test.edu', name='Viewer')
        self.client = APIClient(); self.client.force_authenticate(self.admin)
        self.room = Classroom.objects.create(name='Operations', validated_capacity=20, equipment=['PC'])

    def settings(self, **values):
        return self.client.patch('/api/settings/', values, format='json')

    def test_settings_validation_permissions_and_stale_updates(self):
        self.assertEqual(self.client.get('/api/settings/').data['confidence'], .5)
        self.assertEqual(self.settings(version=0, confidence=.4, auto_save=True).status_code, 200)
        self.assertEqual(self.settings(version=0, confidence=.2).status_code, 400)
        self.assertEqual(self.settings(version=1, confidence=2).status_code, 400)
        self.assertEqual(AdministrativeEvent.objects.count(), 1)
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get('/api/settings/').status_code, 200)
        self.assertEqual(self.settings(version=1, confidence=.3).status_code, 403)
        self.assertEqual(self.client.get('/api/administrative-events/').status_code, 403)

    @patch('video_analysis.live.VisionClient')
    def test_live_options_snapshot_autosave_and_threshold(self, client):
        self.settings(version=0, confidence=.4, auto_save=True, alerts_enabled=True, alert_threshold=80)
        start = self.client.post('/api/live-sessions/', {'classroom': self.room.pk}, format='json')
        ident = start.data['id']
        self.assertEqual(start.data['confidence'], .4)
        self.settings(version=1, alerts_enabled=False)
        # Persist detector-like result to isolate settings/summary behavior, not inference.
        VideoJob.objects.filter(pk=ident).update(result={'people_max': 18})
        stopped = self.client.post(f'/api/live-sessions/{ident}/stop/')
        self.assertIsNotNone(stopped.data['saved_analysis'])
        self.assertEqual(Alert.objects.count(), 1)
        self.assertEqual(self.client.get('/api/alerts/').data['results'][0]['threshold_percent'], 80)
        self.client.post(f'/api/live-sessions/{ident}/stop/')
        self.assertEqual(Alert.objects.count(), 1)

    def test_video_autosave_uses_persisted_options_and_alert_disabled(self):
        job = VideoJob.objects.create(classroom=self.room, creator=self.admin, capacity_snapshot=20,
            video='x.mp4', original_name='x.mp4', options={'auto_save': True, 'alerts_enabled': False})
        client = Mock(); client.status.return_value = {'status': 'completed', 'progress': 100, 'result': {'people_max': 30}}
        synchronize(job, client)
        job.refresh_from_db()
        self.assertIsNotNone(job.saved_analysis_id)
        self.assertEqual(Alert.objects.count(), 0)

    def test_user_access_audit_self_guard_and_session_revocation(self):
        url = f'/api/auth/users/{self.viewer.pk}/access/'
        self.assertEqual(self.client.patch(url, {'role': 'coordinator', 'is_active': False, 'note': 'Cambio del equipo'}, format='json').status_code, 200)
        self.viewer.refresh_from_db(); self.assertFalse(self.viewer.is_active)
        self.assertEqual(self.viewer.role, 'coordinator')
        self.assertEqual(AdministrativeEvent.objects.get().action, 'user.access')
        self.assertEqual(self.client.patch(f'/api/auth/users/{self.admin.pk}/access/', {'role': 'viewer', 'is_active': False, 'note': 'Cambio propio'}, format='json').status_code, 400)
        root = User.objects.create_superuser(email='root@test.edu', name='Root')
        self.assertEqual(self.client.patch(f'/api/auth/users/{root.pk}/access/', {'role': 'viewer', 'is_active': False, 'note': 'Cambio root'}, format='json').status_code, 400)
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.patch(url, {'role': 'admin', 'is_active': True, 'note': 'Intento propio'}, format='json').status_code, 403)

    def schedule(self):
        teacher = Teacher.objects.create(name='Teacher', email='ops-teacher@test.edu')
        subject = Subject.objects.create(code='OPS', name='Operations')
        course = Course.objects.create(code='OPS', name='Operations', teacher=teacher, subject=subject, enrollment=18, required_equipment=['PC'])
        CourseMeeting.objects.create(course=course, weekday=0, start='08:00', end='10:00')
        ClassroomAvailability.objects.create(classroom=self.room, weekday=0, start='08:00', end='12:00')
        day = timezone.localdate(); monday = day + timedelta(days=(7 - day.weekday()) % 7)
        return {'course': course.pk, 'date_from': str(monday), 'date_to': str(monday + timedelta(days=6))}

    def test_rules_restrict_alternatives_validate_values_duplicates_and_audit(self):
        payload = self.schedule()
        response = self.client.post('/api/assignment-rules/', {'kind': 'min_spare', 'value': '3'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(self.client.get('/api/assignments/alternatives/', payload).data['candidates']), 0)
        self.assertEqual(self.client.post('/api/assignment-rules/', {'kind': 'min_spare', 'value': '2'}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/assignment-rules/', {'kind': 'preferred_kind', 'value': 'invalid'}, format='json').status_code, 400)
        url = f"/api/assignment-rules/{response.data['id']}/"
        self.assertEqual(self.client.patch(url, {'version': 0, 'active': False}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(url, {'version': 1, 'active': False}, format='json').status_code, 200)
        self.assertEqual(len(self.client.get('/api/assignments/alternatives/', payload).data['candidates']), 1)
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.post('/api/assignment-rules/', {'kind': 'max_enrollment', 'value': '10'}, format='json').status_code, 403)

    def test_rule_cannot_invalidate_accepted_assignment(self):
        payload = self.schedule()
        proposal = self.client.post('/api/assignments/', payload, format='json')
        self.assertEqual(proposal.status_code, 201)
        self.assertEqual(self.client.post(f"/api/assignments/{proposal.data['id']}/decision/", {'action': 'accept', 'note': 'Aprobado para prueba'}, format='json').status_code, 200)
        response = self.client.post('/api/assignment-rules/', {'kind': 'min_spare', 'value': '3'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AssignmentRule.objects.exists())

    def test_summary_unknown_zero_capacity_and_completed_only(self):
        for capacity, people, status in [(20, 10, 'completed'), (None, 30, 'completed'), (0, 1, 'completed'), (10, 100, 'failed')]:
            VideoJob.objects.create(classroom=self.room, creator=self.admin, status=status, capacity_snapshot=capacity,
                                    original_name='summary.mp4', result={'people_max': people})
        data = self.client.get('/api/analysis-history/summary/').data
        self.assertEqual(data['analyses'], 3); self.assertEqual(data['people_max'], 30)
        self.assertEqual(data['occupancy_mean'], 50); self.assertEqual(data['without_capacity'], 2)
        self.assertEqual(data['over_capacity'], 1)
