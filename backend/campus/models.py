from django.db import models
from django.conf import settings
from django.db.models.functions import Lower


class Classroom(models.Model):
    name = models.CharField(max_length=150, unique=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    kind = models.CharField(max_length=20, choices=[("classroom", "Aula"), ("lab", "Laboratorio")], default="classroom")
    location = models.CharField(max_length=200, blank=True)
    equipment = models.JSONField(default=list, blank=True)
    camera = models.CharField(max_length=20, choices=[("none", "Sin cámara"), ("integrated", "Cámara integrada"), ("usb", "Cámara USB"), ("rtsp", "Cámara IP / RTSP")], default="none")
    camera_label = models.CharField(max_length=100, blank=True)
    validated_capacity = models.PositiveIntegerField(null=True, blank=True)
    capacity_validated_at = models.DateTimeField(null=True, blank=True)
    capacity_validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [models.UniqueConstraint(Lower("name"), name="unique_classroom_name_casefold")]

    def __str__(self):
        return self.name


class CapacityValidation(models.Model):
    classroom = models.ForeignKey(Classroom, related_name="validations", on_delete=models.PROTECT)
    value = models.PositiveIntegerField()
    note = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class ClassroomAvailability(models.Model):
    classroom = models.ForeignKey(Classroom, related_name="availability", on_delete=models.CASCADE)
    weekday = models.PositiveSmallIntegerField()
    start = models.TimeField()
    end = models.TimeField()

    class Meta:
        ordering = ["weekday", "start"]
        constraints = [
            models.CheckConstraint(condition=models.Q(weekday__lte=6), name="availability_valid_weekday"),
            models.CheckConstraint(condition=models.Q(end__gt=models.F("start")), name="availability_positive_interval"),
        ]


class Teacher(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "pk"]
        constraints = [models.UniqueConstraint(Lower("email"), name="unique_teacher_email_casefold")]

    def __str__(self):
        return self.name


class Subject(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "pk"]
        constraints = [models.UniqueConstraint(Lower("code"), name="unique_subject_code_casefold")]

    def __str__(self):
        return self.name


class Course(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT)
    enrollment = models.PositiveIntegerField(default=0)
    required_equipment = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code", "pk"]
        constraints = [models.UniqueConstraint(Lower("code"), name="unique_course_code_casefold")]


class CourseMeeting(models.Model):
    course = models.ForeignKey(Course, related_name="meetings", on_delete=models.CASCADE)
    weekday = models.PositiveSmallIntegerField()
    start = models.TimeField()
    end = models.TimeField()

    class Meta:
        ordering = ["weekday", "start"]
        constraints = [
            models.CheckConstraint(condition=models.Q(weekday__lte=6), name="meeting_valid_weekday"),
            models.CheckConstraint(condition=models.Q(end__gt=models.F("start")), name="meeting_positive_interval"),
        ]


class Analysis(models.Model):
    """Persisted occupancy summary; VideoJob retains detector evidence and context."""
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT)
    people = models.PositiveIntegerField()
    capacity = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=models.PROTECT)
    resolved = models.BooleanField(default=False)
    in_review = models.BooleanField(default=False)
    updated_at = models.DateTimeField(null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")


class AlertEvent(models.Model):
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    previous_status = models.CharField(max_length=10)
    status = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)


class SchedulingLock(models.Model):
    """Single-row mutation gate, including catalog changes affecting assignments."""
    version = models.PositiveBigIntegerField(default=0)


class SystemSettings(models.Model):
    confidence = models.FloatField(default=.5)
    auto_save = models.BooleanField(default=False)
    auto_pdf = models.BooleanField(default=False)
    record_live = models.BooleanField(default=False)
    alerts_enabled = models.BooleanField(default=True)
    alert_threshold = models.PositiveIntegerField(default=100)
    date_format = models.CharField(max_length=10, default='dmy')
    version = models.PositiveIntegerField(default=0)


class AssignmentRule(models.Model):
    kind = models.CharField(max_length=25, unique=True, choices=[
        ('min_spare', 'Puestos de reserva'), ('max_enrollment', 'Matrícula máxima'),
        ('extra_equipment', 'Equipamiento obligatorio'), ('preferred_kind', 'Preferencia de espacio')])
    value = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=0)


class AdministrativeEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=60)
    target = models.CharField(max_length=100)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class AssignmentProposal(models.Model):
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT)
    date_from = models.DateField()
    date_to = models.DateField()
    meetings = models.JSONField()
    course_snapshot = models.JSONField()
    capacity_snapshot = models.PositiveIntegerField()
    preferred_kind = models.CharField(max_length=20, blank=True)
    reasons = models.JSONField(default=list)
    status = models.CharField(max_length=12, default="pending", choices=[
        ("pending", "Pendiente"), ("accepted", "Aceptada"), ("rejected", "Rechazada"), ("cancelled", "Cancelada")])
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.CheckConstraint(condition=models.Q(date_to__gte=models.F("date_from")), name="assignment_valid_dates"),
        ]


class AssignmentDecision(models.Model):
    proposal = models.ForeignKey(AssignmentProposal, related_name="decisions", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=20)
    note = models.CharField(max_length=500)
    before = models.JSONField()
    after = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]
