from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import User
from .models import Alert, Analysis, Classroom


class DashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(email="viewer@example.edu", password="Example!1234", name="Viewer"))

    def test_empty_dashboard_does_not_invent_data(self):
        data = self.client.get("/api/dashboard/").json()
        self.assertEqual(data["classrooms"], 0)
        self.assertEqual(data["analyzed_classrooms"], 0)
        self.assertEqual(data["open_alerts"], 0)
        self.assertTrue(all(row["percent"] is None for row in data["occupancy"]))

    def test_metrics_are_calculated_from_persisted_records(self):
        classroom = Classroom.objects.create(name="Laboratorio", capacity=20)
        Classroom.objects.create(name="Inactiva", active=False)
        analysis = Analysis.objects.create(classroom=classroom, people=25, capacity=20)
        Analysis.objects.create(classroom=classroom, people=15, capacity=20)
        Analysis.objects.create(classroom=classroom, people=3, capacity=0)
        Alert.objects.create(analysis=analysis)
        Alert.objects.create(analysis=analysis, resolved=True)
        data = self.client.get("/api/dashboard/").json()
        self.assertEqual(data["classrooms"], 1)
        self.assertEqual(data["analyzed_classrooms"], 1)
        self.assertEqual(data["open_alerts"], 1)
        day = next(row for row in data["occupancy"] if row["date"] == timezone.localdate().isoformat())
        self.assertEqual(day["percent"], 100)
