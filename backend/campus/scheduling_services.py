from datetime import timedelta
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import AssignmentProposal, AssignmentDecision, Classroom, Course, SchedulingLock, AssignmentRule


def lock_schedule():
    # Must be called inside transaction.atomic. UPDATE also serializes SQLite writers.
    if not SchedulingLock.objects.filter(pk=1).update(version=F("version") + 1):
        SchedulingLock.objects.create(pk=1, version=1)


def slots(course):
    return [{"weekday": m.weekday, "start": m.start.strftime("%H:%M"), "end": m.end.strftime("%H:%M")}
            for m in course.meetings.all()]


def snapshot(course):
    return {"code": course.code, "name": course.name, "teacher_id": course.teacher_id,
            "teacher_name": course.teacher.name, "subject_id": course.subject_id,
            "enrollment": course.enrollment, "required_equipment": course.required_equipment,
            "meetings": slots(course)}


def occurs(weekday, start, end):
    return start + timedelta(days=(weekday - start.weekday()) % 7) <= end


def overlaps(a, b):
    return a["weekday"] == b["weekday"] and a["start"] < b["end"] and b["start"] < a["end"]


def incompatibilities(course, room, meetings, start, end, exclude=None):
    errors = []
    if not course.active or not course.teacher.active or not course.subject.active:
        errors.append("El curso, docente y asignatura deben estar activos.")
    if not room.active:
        errors.append("El aula está inactiva.")
    if course.enrollment <= 0:
        errors.append("Registra una matrícula mayor que cero.")
    if room.validated_capacity is None:
        errors.append("La capacidad del aula no está validada.")
    elif room.validated_capacity < course.enrollment:
        errors.append(f"Capacidad insuficiente: {room.validated_capacity} puestos para {course.enrollment} estudiantes.")
    missing = set(course.required_equipment) - set(room.equipment)
    if missing:
        errors.append("Falta equipamiento: " + ", ".join(sorted(missing)) + ".")
    for rule in AssignmentRule.objects.filter(active=True):
        if rule.kind == 'min_spare' and room.validated_capacity is not None and room.validated_capacity - course.enrollment < int(rule.value):
            errors.append(f'La regla exige {rule.value} puestos de reserva.')
        elif rule.kind == 'max_enrollment' and course.enrollment > int(rule.value):
            errors.append(f'La regla limita la matrícula a {rule.value}.')
        elif rule.kind == 'extra_equipment' and rule.value not in room.equipment:
            errors.append(f'Equipamiento obligatorio por regla: {rule.value}.')
    availability = [{"weekday": a.weekday, "start": a.start.strftime("%H:%M"), "end": a.end.strftime("%H:%M")}
                    for a in room.availability.all()]
    if not meetings or not any(occurs(m["weekday"], start, end) for m in meetings):
        errors.append("No hay sesiones del curso dentro del período seleccionado.")
    for m in meetings:
        if not occurs(m["weekday"], start, end):
            continue
        # Adjacent availability windows form a continuous available interval.
        cursor = m["start"]
        for a in sorted((a for a in availability if a["weekday"] == m["weekday"]), key=lambda a: a["start"]):
            if a["start"] <= cursor < a["end"]:
                cursor = max(cursor, a["end"])
        if cursor < m["end"]:
            errors.append("La disponibilidad declarada del aula no cubre todas las sesiones.")
            break
    others = AssignmentProposal.objects.filter(status="accepted", date_from__lte=end, date_to__gte=start)
    if exclude:
        others = others.exclude(pk=exclude)
    for other in others:
        common_start, common_end = max(start, other.date_from), min(end, other.date_to)
        if any(overlaps(a, b) and occurs(a["weekday"], common_start, common_end)
               for a in meetings for b in other.meetings):
            if other.classroom_id == room.pk:
                errors.append(f"Cruce de aula con la asignación #{other.pk}.")
            if other.course_snapshot["teacher_id"] == course.teacher_id:
                errors.append(f"Cruce de docente con la asignación #{other.pk}.")
            if other.course_id == course.pk:
                errors.append(f"El curso ya está asignado en esa franja (#{other.pk}).")
    return list(dict.fromkeys(errors))


def alternatives(course, start, end, meetings, preferred_kind="", exclude=None):
    if not preferred_kind:
        preference = AssignmentRule.objects.filter(kind='preferred_kind', active=True).first()
        preferred_kind = preference.value if preference else ''
    candidates, excluded = [], []
    for room in Classroom.objects.prefetch_related("availability").order_by("name", "pk"):
        errors = incompatibilities(course, room, meetings, start, end, exclude)
        if errors:
            excluded.append({"classroom": room.pk, "name": room.name, "reasons": errors})
        else:
            spare = room.validated_capacity - course.enrollment
            candidates.append({"classroom": room.pk, "name": room.name, "capacity": room.validated_capacity,
                               "spare": spare, "kind": room.kind,
                               "reasons": ["Capacidad validada suficiente.", "Equipamiento compatible.",
                                           "Disponibilidad completa y sin cruces de aula o docente.",
                                           f"Quedarían {spare} puestos según matrícula."]})
    candidates.sort(key=lambda r: (bool(preferred_kind and r["kind"] != preferred_kind), r["spare"], r["name"], r["classroom"]))
    return {"candidates": candidates, "excluded": excluded}


@transaction.atomic
def propose(data, actor):
    lock_schedule()
    course = Course.objects.select_related("teacher", "subject").get(pk=data["course"].pk)
    meetings = data.get("meetings") or slots(course)
    start, end = data["date_from"], data["date_to"]
    preference = data.get("preferred_kind", "")
    options = alternatives(course, start, end, meetings, preference)
    room_id = data.get("classroom")
    choice = next((r for r in options["candidates"] if room_id is None or r["classroom"] == room_id.pk), None)
    if not choice:
        raise ValidationError({"detail": "No hay un aula compatible para esta propuesta.", "alternatives": options})
    proposal = AssignmentProposal.objects.create(course=course, classroom_id=choice["classroom"],
        date_from=start, date_to=end, meetings=meetings, course_snapshot=snapshot(course),
        capacity_snapshot=choice["capacity"], preferred_kind=preference, reasons=choice["reasons"], creator=actor)
    return proposal


def state(proposal):
    return {"status": proposal.status, "classroom": proposal.classroom_id,
            "meetings": proposal.meetings, "capacity": proposal.capacity_snapshot}


@transaction.atomic
def decide(proposal_id, data, actor):
    lock_schedule()
    proposal = AssignmentProposal.objects.select_related("course__teacher", "course__subject", "classroom").get(pk=proposal_id)
    action = data["action"]
    if (action == "cancel" and proposal.status != "accepted") or (action != "cancel" and proposal.status != "pending"):
        raise ValidationError("La propuesta ya cambió de estado. Actualiza la página; no se registró otra decisión.")
    before = state(proposal)
    if action == "accept":
        if snapshot(proposal.course) != proposal.course_snapshot:
            raise ValidationError("Los datos del curso cambiaron. Rechaza esta propuesta y genera una nueva.")
        room = data.get("classroom", proposal.classroom)
        meetings = data.get("meetings", proposal.meetings)
        errors = incompatibilities(proposal.course, room, meetings, proposal.date_from, proposal.date_to, proposal.pk)
        if errors:
            raise ValidationError(errors)
        proposal.classroom = room
        proposal.meetings = meetings
        proposal.capacity_snapshot = room.validated_capacity
        proposal.status = "accepted"
    else:
        proposal.status = "rejected" if action == "reject" else "cancelled"
    proposal.save()
    AssignmentDecision.objects.create(proposal=proposal, actor=actor, action=action, note=data["note"],
                                      before=before, after=state(proposal))
    return proposal


def validate_assignments():
    """Called after catalog writes inside their transaction; invalid changes roll back."""
    for proposal in AssignmentProposal.objects.filter(status="accepted", date_to__gte=timezone.localdate()).select_related("course__teacher", "course__subject", "classroom"):
        remaining_start = max(proposal.date_from, timezone.localdate())
        if not any(occurs(m["weekday"], remaining_start, proposal.date_to) for m in proposal.meetings):
            continue
        if snapshot(proposal.course) != proposal.course_snapshot or incompatibilities(
                proposal.course, proposal.classroom, proposal.meetings,
                remaining_start, proposal.date_to, proposal.pk):
            raise ValidationError(f"El cambio afecta la asignación vigente #{proposal.pk}. Cancélala en Horarios antes de modificar estos datos.")
