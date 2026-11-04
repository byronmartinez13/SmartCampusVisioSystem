import tempfile
from unittest.mock import Mock
import httpx
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from accounts.models import User
from campus.models import Classroom, Analysis, Alert
from .models import VideoJob
from .services import synchronize


class VideoAnalysisTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        override = override_settings(MEDIA_ROOT=self.temp.name)
        override.enable()
        self.addCleanup(override.disable)
        self.admin = User.objects.create_user(email="admin@video.test", name="Admin", role="admin")
        self.viewer = User.objects.create_user(email="viewer@video.test", name="Viewer")
        self.room = Classroom.objects.create(name="Test room", capacity=30, validated_capacity=20)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def upload(self, content=b"\x00\x00\x00\x20ftypisom" + b"x" * 20):
        return self.client.post("/api/video-analyses/", {
            "classroom": self.room.pk, "activity": "class", "confidence": .5,
            "video": SimpleUploadedFile("sample.mp4", content, "video/mp4")}, format="multipart")

    def job(self):
        response = self.upload()
        self.assertEqual(response.status_code, 202, response.data)
        return VideoJob.objects.get(pk=response.data["id"])

    def test_snapshot_and_no_private_paths_in_api(self):
        job = self.job()
        self.assertEqual(job.capacity_snapshot, 20)
        self.room.validated_capacity = 15
        self.room.save()
        response = self.client.get(f"/api/video-analyses/{job.pk}/")
        self.assertEqual(response.data["capacity_snapshot"], 20)
        self.assertNotIn("video", response.data)
        self.assertNotIn("remote_id", response.data)

    def test_viewers_and_anonymous_cannot_upload_or_save(self):
        job = self.job()
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.upload().status_code, 403)
        self.assertEqual(self.client.post(f"/api/video-analyses/{job.pk}/save-result/").status_code, 403)
        self.assertEqual(self.client.get(f"/api/video-analyses/{job.pk}/").status_code, 200)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"/api/video-analyses/{job.pk}/preview/").status_code, 403)

    def test_invalid_upload_rejected(self):
        self.assertEqual(self.upload(b"fake video").status_code, 400)
        self.assertEqual(VideoJob.objects.count(), 0)

    def test_completed_save_is_idempotent_and_creates_one_alert(self):
        job = self.job()
        client = Mock()
        client.status.return_value = {"status": "completed", "progress": 100, "result": {"people_max": 21}}
        synchronize(job, client)
        for _ in range(2):
            self.assertEqual(self.client.post(f"/api/video-analyses/{job.pk}/save-result/").status_code, 200)
        self.assertEqual(Analysis.objects.count(), 1)
        self.assertEqual(Alert.objects.count(), 1)
        self.assertEqual(Analysis.objects.get().capacity, 20)

    def test_unvalidated_capacity_does_not_invent_occupancy_or_alert(self):
        self.room.validated_capacity = None
        self.room.save()
        job = self.job()
        job.status = "completed"
        job.result = {"people_max": 10}
        job.save()
        self.client.post(f"/api/video-analyses/{job.pk}/save-result/")
        self.assertIsNone(Analysis.objects.get().capacity)
        self.assertEqual(Alert.objects.count(), 0)

    def test_pending_analysis_cannot_be_saved(self):
        job = self.job()
        self.assertEqual(self.client.post(f"/api/video-analyses/{job.pk}/save-result/").status_code, 400)
        self.assertEqual(Analysis.objects.count(), 0)

    def test_cancel_wins_over_stale_worker_and_retry_changes_execution_id(self):
        job = self.job()
        self.client.post(f"/api/video-analyses/{job.pk}/cancel/")
        client = Mock()
        client.status.return_value = {"status": "completed", "progress": 100, "result": {"people_max": 2}}
        synchronize(job, client)
        job.refresh_from_db()
        self.assertEqual(job.status, "cancelling")
        synchronize(job, client)
        job.refresh_from_db()
        self.assertEqual(job.status, "cancelled")
        previous = job.remote_id
        self.assertEqual(self.client.post(f"/api/video-analyses/{job.pk}/retry/").status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.status, "queued")
        self.assertNotEqual(job.remote_id, previous)

    def test_service_failure_is_bounded_and_retryable(self):
        job = self.job()
        client = Mock()
        client.submit.side_effect = httpx.ConnectError("offline")
        with self.assertLogs("video_analysis.services", level="ERROR"):
            for _ in range(3):
                synchronize(job, client)
                job.refresh_from_db()
        self.assertEqual(job.status, "failed")
        self.assertTrue(job.error)

    def test_history_filters_and_invalid_date_range(self):
        job = self.job()
        response = self.client.get("/api/analysis-history/", {"classroom": self.room.pk, "status": "queued", "activity": "class"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(str(response.data["results"][0]["id"]), str(job.pk))
        self.assertEqual(self.client.get("/api/analysis-history/", {"status": "completed"}).data["count"], 0)
        self.assertEqual(self.client.get("/api/analysis-history/", {"date_from": "2026-10-20", "date_to": "2026-01-01"}).status_code, 400)
        self.assertEqual(self.client.get("/api/analysis-history/", {"date_from": "bad"}).status_code, 400)

    def test_history_paginates_without_losing_older_records(self):
        for _ in range(21):
            VideoJob.objects.create(classroom=self.room, creator=self.admin, activity="class", original_name="test.mp4", capacity_snapshot=20)
        first = self.client.get("/api/analysis-history/")
        second = self.client.get("/api/analysis-history/?page=2")
        self.assertEqual(first.data["count"], 21)
        self.assertEqual(len(first.data["results"]), 20)
        self.assertEqual(len(second.data["results"]), 1)

    def test_alert_states_audit_and_dashboard_count(self):
        from campus.models import AlertEvent
        job = self.job()
        job.status = "completed"
        job.result = {"people_max": 21}
        job.save()
        self.client.post(f"/api/video-analyses/{job.pk}/save-result/")
        alert = Alert.objects.get()
        listing = self.client.get("/api/alerts/?status=new")
        self.assertEqual(listing.data["results"][0]["job_id"], str(job.pk))
        for state in ["review", "resolved", "resolved"]:
            response = self.client.post(f"/api/alerts/{alert.pk}/change-status/", {"status": state}, format="json")
            self.assertEqual(response.status_code, 200)
        self.assertEqual(AlertEvent.objects.count(), 2)
        self.assertEqual(self.client.get("/api/alerts/?status=resolved").data["count"], 1)
        self.assertEqual(self.client.get("/api/dashboard/").data["open_alerts"], 0)
        self.client.post(f"/api/alerts/{alert.pk}/change-status/", {"status": "new"}, format="json")
        self.assertEqual(self.client.get("/api/dashboard/").data["open_alerts"], 1)

    def test_alert_permissions_and_status_validation(self):
        analysis = Analysis.objects.create(classroom=self.room, people=30, capacity=20)
        alert = Alert.objects.create(analysis=analysis)
        self.assertIsNone(self.client.get("/api/alerts/").data["results"][0]["job_id"])
        self.assertEqual(self.client.post(f"/api/alerts/{alert.pk}/change-status/", {"status": "invalid"}).status_code, 400)
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get("/api/alerts/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/alerts/{alert.pk}/change-status/", {"status": "resolved"}).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/analysis-history/").status_code, 403)
