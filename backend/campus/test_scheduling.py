from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import User
from .models import Classroom, ClassroomAvailability, Teacher, Subject, Course, CourseMeeting, AssignmentProposal, AssignmentDecision


class SchedulingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="scheduler@test.edu", name="Admin", role="admin")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.teacher = Teacher.objects.create(name="Teacher", email="teacher@test.edu")
        self.subject = Subject.objects.create(name="Software", code="SW")
        self.course = self.make_course("C1")
        self.room = self.make_room("Room", 20)
        today = timezone.localdate()
        self.start = today + timedelta(days=(7 - today.weekday()) % 7)
        self.end = self.start + timedelta(days=6)

    def make_course(self, code, teacher=None):
        course = Course.objects.create(code=code, name=code, subject=self.subject,
                                       teacher=teacher or self.teacher, enrollment=15, required_equipment=["computadores"])
        CourseMeeting.objects.create(course=course, weekday=0, start="08:00", end="10:00")
        return course

    def make_room(self, name, capacity, kind="classroom"):
        room = Classroom.objects.create(name=name, capacity=capacity, validated_capacity=capacity,
                                         equipment=["computadores"], kind=kind)
        ClassroomAvailability.objects.create(classroom=room, weekday=0, start="08:00", end="12:00")
        return room

    def payload(self, **extra):
        return {"course": self.course.pk, "date_from": self.start.isoformat(), "date_to": self.end.isoformat(), **extra}

    def propose(self, **extra):
        response = self.client.post("/api/assignments/", self.payload(**extra), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data["id"]

    def decide(self, id, action="accept", **extra):
        return self.client.post(f"/api/assignments/{id}/decision/",
                                {"action": action, "note": "Revisión académica completa", **extra}, format="json")

    def test_alternatives_reject_unknown_capacity_equipment_and_unavailable_rooms(self):
        unknown = self.make_room("Unknown", None)
        missing = self.make_room("Missing", 20)
        missing.equipment = []
        missing.save()
        unavailable = self.make_room("Unavailable", 20)
        unavailable.availability.all().delete()
        response = self.client.get("/api/assignments/alternatives/", self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["classroom"] for r in response.data["candidates"]], [self.room.pk])
        self.assertEqual(len(response.data["excluded"]), 3)

    def test_soft_preference_orders_only_compatible_rooms(self):
        lab = self.make_room("Lab", 30, "lab")
        self.make_room("Small lab", 2, "lab")
        response = self.client.get("/api/assignments/alternatives/", self.payload(preferred_kind="lab"))
        self.assertEqual(response.data["candidates"][0]["classroom"], lab.pk)

    def test_pending_not_reserved_accept_is_revalidated_and_duplicate_blocked(self):
        first, second = self.propose(), self.propose()
        self.assertEqual(self.decide(first).status_code, 200)
        self.assertEqual(self.decide(first).status_code, 400)
        self.assertEqual(self.decide(second).status_code, 400)
        self.assertEqual(AssignmentDecision.objects.count(), 1)

    def test_conflicts_by_teacher_even_in_another_room_and_contiguous_allowed(self):
        self.assertEqual(self.decide(self.propose()).status_code, 200)
        other_room = self.make_room("Other", 20)
        second_course = self.make_course("C2")
        response = self.client.post("/api/assignments/", self.payload(course=second_course.pk, classroom=other_room.pk), format="json")
        self.assertEqual(response.status_code, 400)
        meetings = [{"weekday": 0, "start": "10:00", "end": "11:00"}]
        second = self.propose(course=second_course.pk, classroom=other_room.pk, meetings=meetings)
        self.assertEqual(self.decide(second).status_code, 200)

    def test_room_collision_with_different_teachers(self):
        teacher = Teacher.objects.create(name="Other", email="other@test.edu")
        other = self.make_course("C2", teacher)
        first = self.propose()
        second = self.propose(course=other.pk)
        self.decide(first)
        self.assertEqual(self.decide(second).status_code, 400)

    def test_separate_periods_do_not_conflict(self):
        self.decide(self.propose())
        id = self.propose(date_from=(self.start + timedelta(days=7)).isoformat(),
                          date_to=(self.end + timedelta(days=7)).isoformat())
        self.assertEqual(self.decide(id).status_code, 200)

    def test_modify_accept_audit_calendar_and_cancel(self):
        id = self.propose()
        new = [{"weekday": 0, "start": "09:00", "end": "11:00"}]
        self.assertEqual(self.decide(id, meetings=new).status_code, 200)
        response = self.client.get("/api/assignments/calendar/", {"classroom": self.room.pk, "week": self.start.isoformat()})
        self.assertEqual(response.data["sessions"][0]["percent"], 75)
        self.assertEqual(response.data["sessions"][0]["start"], "09:00")
        event = AssignmentDecision.objects.get()
        self.assertEqual(event.before["meetings"][0]["start"], "08:00")
        self.assertEqual(event.after["meetings"][0]["start"], "09:00")
        self.assertEqual(self.decide(id, "cancel").status_code, 200)
        self.assertEqual(self.client.get("/api/assignments/calendar/", {"classroom": self.room.pk, "week": self.start.isoformat()}).data["sessions"], [])

    def test_reject_requires_note_and_cannot_be_accepted_later(self):
        id = self.propose()
        self.assertEqual(self.client.post(f"/api/assignments/{id}/decision/", {"action": "reject", "note": ""}).status_code, 400)
        self.assertEqual(self.decide(id, "reject").status_code, 200)
        self.assertEqual(self.decide(id).status_code, 400)

    def test_stale_course_or_capacity_prevents_acceptance(self):
        id = self.propose()
        self.course.enrollment = 21
        self.course.save()
        self.assertEqual(self.decide(id).status_code, 400)
        self.course.enrollment = 15
        self.course.save()
        self.room.validated_capacity = 14
        self.room.save()
        self.assertEqual(self.decide(id).status_code, 400)

    def test_catalog_edits_cannot_invalidate_accepted_assignment(self):
        id = self.propose()
        self.decide(id)
        response = self.client.patch(f"/api/classrooms/{self.room.pk}/", {"availability": []}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.room.availability.count(), 1)
        response = self.client.patch(f"/api/courses/{self.course.pk}/", {"enrollment": 25}, format="json")
        self.assertEqual(response.status_code, 400)
        self.course.refresh_from_db()
        self.assertEqual(self.course.enrollment, 15)
        self.decide(id, "cancel")
        self.assertEqual(self.client.patch(f"/api/classrooms/{self.room.pk}/", {"availability": []}, format="json").status_code, 200)

    def test_invalid_intervals_dates_and_no_occurrences_rejected(self):
        for extra in [{"date_to": (self.start - timedelta(days=1)).isoformat()},
                      {"date_to": (self.start + timedelta(days=366)).isoformat()},
                      {"meetings": []},
                      {"meetings": [{"weekday": 0, "start": "10:00", "end": "08:00"}]},
                      {"date_from": (self.start + timedelta(days=1)).isoformat()}]:
            self.assertEqual(self.client.post("/api/assignments/", self.payload(**extra), format="json").status_code, 400)

    def test_roles_allow_coordinator_but_viewer_is_read_only(self):
        viewer = User.objects.create_user(email="viewer@schedule.edu", name="Viewer", role="viewer")
        self.client.force_authenticate(viewer)
        self.assertEqual(self.client.get("/api/assignments/alternatives/", self.payload()).status_code, 200)
        self.assertEqual(self.client.post("/api/assignments/", self.payload(), format="json").status_code, 403)
        viewer.role = "coordinator"
        viewer.save()
        self.assertEqual(self.client.post("/api/assignments/", self.payload(), format="json").status_code, 201)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/assignments/").status_code, 403)
