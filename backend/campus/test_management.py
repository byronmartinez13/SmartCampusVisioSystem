from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from .models import Classroom, ClassroomAvailability, CapacityValidation, Course, CourseMeeting, Subject, Teacher


class CampusManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(email="admin@example.edu", password="Campus!12345", name="Admin", role="admin")
        cls.viewer = User.objects.create_user(email="viewer@example.edu", password="Campus!12345", name="Viewer")
        cls.coordinator = User.objects.create_user(email="coord@example.edu", name="Coordinator", role="coordinator")
        cls.teacher = Teacher.objects.create(name="Docente Uno", email="docente@example.edu")
        cls.subject = Subject.objects.create(name="Construcción", code="CS101")

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(self.admin)
        self.room_data = {
            "name": "Semillero", "kind": "lab", "capacity": 30, "equipment": ["Computadores", "Proyector"],
            "camera": "usb", "camera_label": "Cámara 01",
            "availability": [{"weekday": 0, "start": "08:00", "end": "12:00"}],
        }
        self.course_data = {
            "name": "Quinto A", "code": "CS5A", "subject": self.subject.pk, "teacher": self.teacher.pk,
            "enrollment": 25, "meetings": [{"weekday": 0, "start": "08:00", "end": "10:00"}],
        }

    def post(self, resource, data):
        return self.client.post(f"/api/{resource}/", data, format="json")

    def patch(self, resource, pk, data):
        return self.client.patch(f"/api/{resource}/{pk}/", data, format="json")

    def test_anonymous_and_readonly_roles(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/classrooms/").status_code, 403)
        for user in (self.viewer, self.coordinator):
            self.client.force_login(user)
            for resource in ("classrooms", "courses", "teachers", "subjects"):
                self.assertEqual(self.client.get(f"/api/{resource}/").status_code, 200)
                self.assertEqual(self.post(resource, {}).status_code, 403)
        self.assertEqual(Classroom.objects.count(), 0)

    def test_classroom_create_filter_edit_and_dashboard(self):
        result = self.post("classrooms", self.room_data)
        self.assertEqual(result.status_code, 201, result.data)
        room = Classroom.objects.get()
        self.assertEqual(room.equipment, ["computadores", "proyector"])
        self.assertEqual(room.availability.count(), 1)
        self.assertEqual(self.client.get("/api/classrooms/?kind=lab&search=Semill").json()[0]["id"], room.pk)
        self.assertEqual(self.client.get("/api/classrooms/?kind=classroom").json(), [])
        self.assertEqual(self.client.get("/api/dashboard/").json()["classrooms"], 1)
        self.assertEqual(self.patch("classrooms", room.pk, {"active": False}).status_code, 200)
        self.assertEqual(self.client.get("/api/dashboard/").json()["classrooms"], 0)
        self.assertEqual(self.client.get("/api/classrooms/?active=true").json(), [])
        self.assertEqual(self.client.delete(f"/api/classrooms/{room.pk}/").status_code, 405)

    def test_case_insensitive_duplicates(self):
        self.post("classrooms", self.room_data)
        self.assertEqual(self.post("classrooms", {**self.room_data, "name": "semillero"}).status_code, 400)
        self.assertEqual(self.post("teachers", {"name": "Duplicate", "email": "DOCENTE@EXAMPLE.EDU"}).status_code, 400)
        self.assertEqual(self.post("subjects", {"name": "Duplicate", "code": "cs101"}).status_code, 400)
        self.post("courses", self.course_data)
        self.assertEqual(self.post("courses", {**self.course_data, "code": "cs5a"}).status_code, 400)

    def test_invalid_capacity_and_equipment(self):
        for value in (-1, 2.5, "bad"):
            self.assertEqual(self.post("classrooms", {**self.room_data, "capacity": value}).status_code, 400)
        self.assertEqual(self.post("classrooms", {**self.room_data, "equipment": "not a list"}).status_code, 400)
        self.assertEqual(Classroom.objects.count(), 0)

    def test_invalid_intervals_are_atomic(self):
        cases = [
            [{"weekday": 7, "start": "08:00", "end": "10:00"}],
            [{"weekday": 0, "start": "10:00", "end": "10:00"}],
            [{"weekday": 0, "start": "23:00", "end": "01:00"}],
            [{"weekday": 0, "start": "08:00", "end": "10:00"}, {"weekday": 0, "start": "09:00", "end": "11:00"}],
        ]
        for slots in cases:
            self.assertEqual(self.post("classrooms", {**self.room_data, "availability": slots}).status_code, 400)
        self.assertEqual(Classroom.objects.count(), 0)
        self.assertEqual(ClassroomAvailability.objects.count(), 0)

    def test_validation_audit_and_invalidation_on_physical_changes(self):
        room = Classroom.objects.create(name="Aula", capacity=30)
        self.patch("classrooms", room.pk, {"validated_capacity": 99})
        room.refresh_from_db()
        self.assertIsNone(room.validated_capacity)
        result = self.post(f"classrooms/{room.pk}/validate-capacity", {"value": 28, "note": "Conteo manual de puestos"})
        self.assertEqual(result.status_code, 200, result.data)
        room.refresh_from_db()
        self.assertEqual(room.validated_capacity, 28)
        self.assertEqual(room.capacity_validated_by, self.admin)
        self.assertEqual(CapacityValidation.objects.get().value, 28)
        self.patch("classrooms", room.pk, {"name": "Aula renombrada"})
        room.refresh_from_db()
        self.assertEqual(room.validated_capacity, 28)
        response = self.patch("classrooms", room.pk, {"capacity": 35})
        self.assertEqual(response.json(), self.client.get(f"/api/classrooms/{room.pk}/").json())
        room.refresh_from_db()
        self.assertIsNone(room.validated_capacity)
        self.assertEqual(CapacityValidation.objects.count(), 1)
        self.client.force_login(self.viewer)
        self.assertEqual(self.post(f"classrooms/{room.pk}/validate-capacity", {"value": 100, "note": "Intento sin permiso"}).status_code, 403)

    def test_capacity_validation_zero_and_empty_note(self):
        room = Classroom.objects.create(name="Empty")
        self.assertEqual(self.post(f"classrooms/{room.pk}/validate-capacity", {"value": 0, "note": "Espacio vacío"}).status_code, 200)
        self.assertEqual(self.post(f"classrooms/{room.pk}/validate-capacity", {"value": 1, "note": ""}).status_code, 400)
        self.assertEqual(CapacityValidation.objects.count(), 1)

    def test_course_creation_and_enrollment_updates(self):
        result = self.post("courses", self.course_data)
        self.assertEqual(result.status_code, 201, result.data)
        course = Course.objects.get()
        self.assertEqual(course.meetings.count(), 1)
        self.assertEqual(self.patch("courses", course.pk, {"enrollment": 0}).status_code, 200)
        course.refresh_from_db()
        self.assertEqual(course.enrollment, 0)
        for value in (-1, 1.5, "", "not-a-number"):
            self.assertEqual(self.patch("courses", course.pk, {"enrollment": value}).status_code, 400)
        course.refresh_from_db()
        self.assertEqual(course.enrollment, 0)
        self.assertEqual(course.meetings.count(), 1)

    def test_conflict_and_adjacent_teacher_intervals(self):
        self.post("courses", self.course_data)
        overlapping = {**self.course_data, "code": "CS5B", "meetings": [{"weekday": 0, "start": "09:00", "end": "11:00"}]}
        result = self.post("courses", overlapping)
        self.assertEqual(result.status_code, 400)
        self.assertIn("conflicto", str(result.data))
        self.assertEqual(Course.objects.count(), 1)
        adjacent = {**overlapping, "meetings": [{"weekday": 0, "start": "10:00", "end": "12:00"}]}
        self.assertEqual(self.post("courses", adjacent).status_code, 201)

    def test_course_update_conflict_preserves_previous_data(self):
        self.post("courses", self.course_data)
        second = self.post("courses", {**self.course_data, "code": "CS5B", "meetings": [{"weekday": 0, "start": "10:00", "end": "12:00"}]})
        result = self.patch("courses", second.data["id"], {"name": "Should not save", "meetings": [{"weekday": 0, "start": "09:00", "end": "12:00"}]})
        self.assertEqual(result.status_code, 400)
        second_course = Course.objects.get(pk=second.data["id"])
        self.assertEqual(second_course.name, "Quinto A")
        self.assertEqual(str(second_course.meetings.get().start), "10:00:00")

    def test_inactive_course_and_reactivation_conflict(self):
        self.post("courses", self.course_data)
        second = self.post("courses", {**self.course_data, "code": "INACTIVE", "active": False})
        self.assertEqual(second.status_code, 201)
        self.assertEqual(self.patch("courses", second.data["id"], {"active": True}).status_code, 400)
        self.assertFalse(Course.objects.get(pk=second.data["id"]).active)

    def test_cannot_deactivate_catalog_used_by_active_course(self):
        self.post("courses", self.course_data)
        self.assertEqual(self.patch("teachers", self.teacher.pk, {"active": False}).status_code, 400)
        self.assertEqual(self.patch("subjects", self.subject.pk, {"active": False}).status_code, 400)
        self.patch("courses", Course.objects.get().pk, {"active": False})
        self.assertEqual(self.patch("teachers", self.teacher.pk, {"active": False}).status_code, 200)
        self.assertEqual(self.patch("courses", Course.objects.get().pk, {"active": True}).status_code, 400)

    def test_missing_references_rejected(self):
        self.assertEqual(self.post("courses", {**self.course_data, "teacher": 99999}).status_code, 400)
        self.assertEqual(self.post("courses", {**self.course_data, "subject": 99999}).status_code, 400)

    def test_no_fake_activity_for_new_classroom(self):
        room = Classroom.objects.create(name="Sin análisis")
        self.assertEqual(self.client.get(f"/api/classrooms/{room.pk}/activity/").json(), [])

    def test_writes_require_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post("/api/classrooms/", self.room_data, format="json").status_code, 403)

    def test_e2e_seed_rejected_outside_test_settings(self):
        with self.assertRaises(CommandError):
            call_command("prepare_e2e")

    def test_local_role_command_does_not_grant_django_staff(self):
        call_command("set_role", self.viewer.email, "admin", verbosity=0)
        self.viewer.refresh_from_db()
        self.assertEqual(self.viewer.role, "admin")
        self.assertFalse(self.viewer.is_staff)
