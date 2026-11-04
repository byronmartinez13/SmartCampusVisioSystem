import logging
import httpx
from django.db import transaction
from django.utils import timezone
from campus.models import Analysis, Alert
from rest_framework.exceptions import ValidationError
from .models import VideoJob

logger = logging.getLogger(__name__)
ACTIVE = ("queued", "processing", "cancelling")


def synchronize(job, client):
    """Single dispatcher process, conditional writes preserve concurrent cancellation."""
    if job.source == 'camera':
        return
    try:
        if job.status == "cancelling":
            client.cancel(job)
            VideoJob.objects.filter(pk=job.pk, status="cancelling").update(
                status="cancelled", error="", updated_at=timezone.now())
            return
        if job.status == "queued":
            client.submit(job)
        remote = client.status(job)
        status = remote["status"]
        if status not in ("queued", "processing", "completed", "failed", "cancelled"):
            raise ValueError("Invalid remote state")
        result = remote.get("result")
        if status == "completed":
            if not isinstance(result, dict) or not isinstance(result.get("people_max"), int) or result["people_max"] < 0:
                raise ValueError("Invalid detector result")
        VideoJob.objects.filter(pk=job.pk, status__in=("queued", "processing")).update(
            status="processing" if status == "queued" else status,
            progress=max(0, min(100, int(remote["progress"]))),
            result=result, error=remote.get("error", ""), attempts=0, updated_at=timezone.now())
        if status == 'completed' and job.options.get('auto_save'):
            current = VideoJob.objects.get(pk=job.pk)
            if current.status == 'completed':
                save_summary(current.pk)
    except (httpx.HTTPError, ValueError, KeyError, OSError):
        logger.exception("Vision synchronization failed for %s", job.pk)
        attempts = job.attempts + 1
        VideoJob.objects.filter(pk=job.pk, status=job.status).update(
            attempts=attempts,
            status="failed" if attempts >= 3 and job.status != "cancelling" else job.status,
            error="No se pudo comunicar o procesar el video con el servicio de visión. Revisa el servicio y vuelve a intentarlo.",
            updated_at=timezone.now())


@transaction.atomic
def save_summary(job_id):
    job = VideoJob.objects.select_for_update().get(pk=job_id)
    if job.saved_analysis_id:
        return job
    if job.status != "completed" or not job.result:
        raise ValidationError("El análisis debe estar completado para guardar el resultado.")
    analysis = Analysis.objects.create(classroom=job.classroom,
                                       people=job.result["people_max"], capacity=job.capacity_snapshot)
    if (job.options.get('alerts_enabled', True) and job.capacity_snapshot is not None
            and analysis.people * 100 > job.capacity_snapshot * job.options.get('alert_threshold', 100)):
        Alert.objects.create(analysis=analysis)
    job.saved_analysis = analysis
    job.save(update_fields=["saved_analysis", "updated_at"])
    return job
