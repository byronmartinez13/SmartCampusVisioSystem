from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import CapacityValidation, Classroom, ClassroomAvailability, Course, CourseMeeting, Subject, Teacher
from .scheduling_services import lock_schedule, validate_assignments


@transaction.atomic
def save_classroom(data, instance=None):
    lock_schedule()
    availability = data.pop("availability", None)
    if instance:
        instance = Classroom.objects.select_for_update().get(pk=instance.pk)
        # Declared capacity or physical equipment changed: human validation must be repeated.
        if any(key in data and data[key] != getattr(instance, key) for key in ("capacity", "equipment", "kind")):
            instance.validated_capacity = None
            instance.capacity_validated_at = None
            instance.capacity_validated_by = None
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
    else:
        instance = Classroom.objects.create(**data)
    if availability is not None:
        instance.availability.all().delete()
        ClassroomAvailability.objects.bulk_create([ClassroomAvailability(classroom=instance, **row) for row in availability])
    validate_assignments()
    return instance


@transaction.atomic
def validate_capacity(classroom_id, data, actor):
    lock_schedule()
    classroom = Classroom.objects.select_for_update().get(pk=classroom_id)
    CapacityValidation.objects.create(classroom=classroom, actor=actor, **data)
    classroom.validated_capacity = data["value"]
    classroom.capacity_validated_at = timezone.now()
    classroom.capacity_validated_by = actor
    classroom.save(update_fields=["validated_capacity", "capacity_validated_at", "capacity_validated_by"])
    validate_assignments()
    return classroom


def intervals_overlap(a, b):
    return a["weekday"] == b.weekday and a["start"] < b.end and b.start < a["end"]


@transaction.atomic
def save_course(data, instance=None):
    lock_schedule()
    # Serialize mutations for a shared teacher. Production uses row locks in PostgreSQL.
    teacher_id = data.get("teacher", instance.teacher if instance else None).pk
    teacher = Teacher.objects.select_for_update().get(pk=teacher_id)
    subject_id = data.get("subject", instance.subject if instance else None).pk
    subject = Subject.objects.select_for_update().get(pk=subject_id)
    if instance:
        instance = Course.objects.select_for_update().get(pk=instance.pk)
    active = data.get("active", instance.active if instance else True)
    meetings = data.pop("meetings", None)
    effective_meetings = meetings if meetings is not None else [
        {"weekday": m.weekday, "start": m.start, "end": m.end} for m in instance.meetings.all()
    ] if instance else []
    if active and (not teacher.active or not subject.active):
        raise ValidationError("Un curso activo requiere docente y asignatura activos.")
    if active:
        others = CourseMeeting.objects.filter(course__active=True, course__teacher=teacher)
        if instance:
            others = others.exclude(course=instance)
        for meeting in others.select_related("course"):
            if any(intervals_overlap(slot, meeting) for slot in effective_meetings):
                raise ValidationError(f"El docente tiene un conflicto de horario con el curso {meeting.course.code}.")
    if instance:
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
    else:
        instance = Course.objects.create(**data)
    if meetings is not None:
        instance.meetings.all().delete()
        CourseMeeting.objects.bulk_create([CourseMeeting(course=instance, **row) for row in meetings])
    validate_assignments()
    return instance


@transaction.atomic
def save_catalog(serializer):
    lock_schedule()
    instance = serializer.instance
    if instance:
        model = type(instance)
        instance = model.objects.select_for_update().get(pk=instance.pk)
        serializer.instance = instance
        if serializer.validated_data.get("active") is False:
            relation = "teacher" if model is Teacher else "subject"
            if Course.objects.filter(**{relation: instance}, active=True).exists():
                raise ValidationError("Primero desactiva o reasigna los cursos activos asociados.")
    result = serializer.save()
    validate_assignments()
    return result
