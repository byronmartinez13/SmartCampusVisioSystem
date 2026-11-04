import uuid
import httpx
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from campus.permissions import ReadOrAdmin
from .client import VisionClient
from .models import VideoJob
from .serializers import JobSerializer, UploadSerializer
from .services import save_summary


class VideoJobViewSet(viewsets.GenericViewSet):
    permission_classes = [ReadOrAdmin]
    serializer_class = JobSerializer
    queryset = VideoJob.objects.select_related("classroom", "course", "creator").all()

    def list(self, request):
        return Response(JobSerializer(self.get_queryset()[:100], many=True).data)

    def retrieve(self, request, pk=None):
        return Response(JobSerializer(self.get_object()).data)

    @action(detail=True, methods=["get"], url_path="report")
    def report(self, request, pk=None):
        from .reports import report_pdf
        job = self.get_object()
        if job.status != "completed" or not job.result or "people_max" not in job.result:
            raise ValidationError("El PDF requiere un análisis completado con resultados.")
        return report_pdf([job], individual=True)

    def create(self, request):
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if VideoJob.objects.filter(source='video', status__in=["queued", "processing", "cancelling"]).count() >= 10:
            raise ValidationError("Hay diez videos pendientes. Espera a que finalice alguno.")
        classroom = serializer.validated_data["classroom"]
        from campus.operations import analysis_options
        options = analysis_options()
        job = serializer.save(creator=request.user,
                              options=options, confidence=serializer.validated_data.get('confidence', options['confidence']),
                              original_name=serializer.validated_data["video"].name[:255],
                              capacity_snapshot=classroom.validated_capacity)
        return Response(JobSerializer(job).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        job = self.get_object()
        VideoJob.objects.filter(pk=job.pk, status__in=["queued", "processing"]).update(
            status="cancelled" if job.source == 'camera' else "cancelling", updated_at=timezone.now())
        job.refresh_from_db()
        return Response(JobSerializer(job).data)

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        job = self.get_object()
        if job.source == 'camera':
            raise ValidationError('Inicia una nueva sesión de cámara desde Análisis en vivo.')
        if job.status not in ("failed", "cancelled"):
            raise ValidationError("Solo se pueden reintentar análisis fallidos o cancelados.")
        VideoJob.objects.filter(pk=job.pk, status__in=["failed", "cancelled"]).update(
            remote_id=uuid.uuid4(), status="queued", progress=0, result=None, error="", attempts=0,
            updated_at=timezone.now())
        job.refresh_from_db()
        return Response(JobSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="save-result")
    def save_result(self, request, pk=None):
        job = save_summary(self.get_object().pk)
        return Response(JobSerializer(job).data)

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        job = self.get_object()
        if job.source == 'camera':
            return Response({'detail': 'Los fotogramas en vivo no se conservan.'}, status=404)
        client = VisionClient()
        try:
            return HttpResponse(client.preview(job), content_type="image/jpeg",
                                headers={"Cache-Control": "private, no-store"})
        except httpx.HTTPError:
            return Response({"detail": "Imagen aún no disponible."}, status=404)
        finally:
            client.close()
