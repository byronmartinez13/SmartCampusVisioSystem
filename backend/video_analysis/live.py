"""Browser camera sessions: inference server-side, frames never persisted."""
import httpx
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.permissions import IsAdministrator
from campus.models import Classroom, Course
from .client import VisionClient
from .models import VideoJob
from .serializers import JobSerializer


class Start(serializers.Serializer):
    classroom = serializers.PrimaryKeyRelatedField(queryset=Classroom.objects.filter(active=True))
    activity = serializers.ChoiceField(choices=['class', 'exam', 'practice', 'other'], default='class')
    confidence = serializers.FloatField(min_value=.1, max_value=.95, required=False)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.filter(active=True), required=False, allow_null=True)


class LiveViewSet(viewsets.ViewSet):
    permission_classes = [IsAdministrator]

    def session(self, request, pk):
        return get_object_or_404(VideoJob, pk=pk, source='camera', creator=request.user)

    def create(self, request):
        data = Start(data=request.data)
        data.is_valid(raise_exception=True)
        from campus.operations import analysis_options
        options = analysis_options()
        values = dict(data.validated_data)
        values.setdefault('confidence', options['confidence'])
        job = VideoJob.objects.create(**values, options=options, source='camera', creator=request.user,
            status='processing', original_name='Sesión de cámara',
            capacity_snapshot=data.validated_data['classroom'].validated_capacity)
        return Response(JobSerializer(job).data, status=201)

    @action(detail=True, methods=['post'])
    def frame(self, request, pk=None):
        job = self.session(request, pk)
        if job.status != 'processing' or (timezone.now() - job.created_at).total_seconds() > 600:
            raise serializers.ValidationError('Sesión detenida o límite de 10 minutos alcanzado. Detén y guarda la sesión.')
        image = request.FILES.get('image')
        if not image or not 0 < image.size <= 2 * 1024 * 1024:
            raise serializers.ValidationError('Selecciona una imagen JPEG de hasta 2 MB.')
        if job.result and job.result['sampled_frames'] >= 1000:
            raise serializers.ValidationError('Límite de 1000 muestras alcanzado. Detén la sesión.')
        client = VisionClient()
        try:
            detected = client.frame(image.read(), job.confidence)
        except httpx.HTTPError:
            return Response({'detail': 'El servicio de visión no está disponible u ocupado. Revisa el servicio e intenta de nuevo.'}, status=503)
        finally:
            client.close()
        previous = job.result
        if previous and previous['detector'] != detected['detector']:
            raise serializers.ValidationError('El modelo cambió durante la sesión. Inicia una nueva sesión.')
        samples = list(previous['samples']) if previous else []
        sample = {'frame': len(samples), 'seconds': round((timezone.now() - job.created_at).total_seconds(), 2),
                  'people': detected['people'], 'seats': detected['seats']}
        samples.append(sample)
        peak = sample if not previous or sample['people'] > previous['people_max'] else previous['peak_sample']
        result = {'people_max': max(s['people'] for s in samples), 'people_mean': round(sum(s['people'] for s in samples) / len(samples), 2),
                  'seats_max': max(s['seats'] for s in samples), 'samples': samples, 'sampled_frames': len(samples),
                  'peak_sample': peak, 'detector': detected['detector'], 'processing_seconds': 0,
                  'video': {'duration_seconds': sample['seconds'], 'width': detected['width'], 'height': detected['height'], 'fps': None}}
        # Compare-and-swap rejects overlapping requests and results arriving after stop.
        changed = VideoJob.objects.filter(pk=job.pk, status='processing', updated_at=job.updated_at).update(result=result, updated_at=timezone.now())
        if not changed:
            return Response({'detail': 'La sesión cambió durante la detección.'}, status=409)
        return Response({**detected, 'samples': len(samples), 'people_max': result['people_max']}, headers={'Cache-Control': 'no-store'})

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        job = self.session(request, pk)
        if job.status == 'processing':
            # A concurrent first frame cannot make a cancelled session appear completed.
            VideoJob.objects.filter(pk=job.pk, status='processing', updated_at=job.updated_at).update(
                status='completed' if job.result else 'cancelled', progress=100 if job.result else 0, updated_at=timezone.now())
            job.refresh_from_db()
            if job.status == 'processing':
                return Response({'detail': 'Espera a que termine la muestra y vuelve a detener.'}, status=409)
        if job.status == 'completed' and job.options.get('auto_save'):
            from .services import save_summary
            job = save_summary(job.pk)
        return Response(JobSerializer(job).data)
