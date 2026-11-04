import uuid
from pathlib import Path
from django.conf import settings
from django.db import models


def upload_path(instance, filename):
    return f"videos/{instance.id}/input{Path(filename).suffix.lower()}"


class VideoJob(models.Model):
    options = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=10, default='video', choices=[('video', 'Video'), ('camera', 'Cámara')])
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    remote_id = models.UUIDField(default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey("campus.Classroom", on_delete=models.PROTECT)
    course = models.ForeignKey("campus.Course", null=True, blank=True, on_delete=models.PROTECT)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    activity = models.CharField(max_length=20, choices=[
        ("class", "Clase"), ("exam", "Evaluación"), ("practice", "Práctica"), ("other", "Otra")])
    video = models.FileField(upload_to=upload_path)
    original_name = models.CharField(max_length=255)
    confidence = models.FloatField(default=.5)
    capacity_snapshot = models.PositiveIntegerField(null=True)
    status = models.CharField(max_length=20, default="queued", choices=[
        (s, s) for s in ("queued", "processing", "completed", "failed", "cancelling", "cancelled")])
    progress = models.PositiveSmallIntegerField(default=0)
    error = models.TextField(blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    result = models.JSONField(null=True)
    saved_analysis = models.OneToOneField("campus.Analysis", null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
