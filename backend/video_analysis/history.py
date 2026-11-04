from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from campus.models import Alert, AlertEvent
from campus.permissions import ReadOrAdmin
from .models import VideoJob
from .serializers import JobSerializer


class Filters(serializers.Serializer):
    course = serializers.IntegerField(min_value=1, required=False)
    source = serializers.ChoiceField(choices=['video', 'camera'], required=False)
    classroom = serializers.IntegerField(min_value=1, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    activity = serializers.ChoiceField(choices=["class", "exam", "practice", "other"], required=False)
    status = serializers.ChoiceField(choices=["queued", "processing", "completed", "failed", "cancelling", "cancelled"], required=False)

    def validate(self, data):
        if data.get("date_from") and data.get("date_to") and data["date_from"] > data["date_to"]:
            raise serializers.ValidationError("La fecha inicial debe ser anterior o igual a la final.")
        return data


class Pages(PageNumberPagination):
    page_size = 20


def filtered_jobs(params):
    filters = Filters(data={k: v for k, v in params.items() if v and k != "page"})
    filters.is_valid(raise_exception=True)
    qs = VideoJob.objects.select_related("classroom", "course", "creator")
    for key, value in filters.validated_data.items():
        field = {"date_from": "created_at__date__gte", "date_to": "created_at__date__lte"}.get(key, key)
        qs = qs.filter(**{field: value})
    return qs.order_by("-created_at", "-id")


class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [ReadOrAdmin]
    serializer_class = JobSerializer
    pagination_class = Pages

    def get_queryset(self):
        return filtered_jobs(self.request.query_params)

    def report_jobs(self):
        jobs = list(self.get_queryset().filter(status='completed', result__isnull=False)[:501])
        if len(jobs) > 500:
            raise serializers.ValidationError('El reporte admite hasta 500 análisis. Reduce el rango de fechas o filtra por aula.')
        return jobs

    @action(detail=False, methods=['get'])
    def summary(self, request):
        from .reporting import summarize
        return Response(summarize(self.report_jobs()))

    @action(detail=False, methods=["get"], url_path="report")
    def report(self, request):
        from .reports import report_pdf
        jobs = self.report_jobs()
        return report_pdf(jobs, filters=request.query_params)


def alert_status(alert):
    return "resolved" if alert.resolved else "review" if alert.in_review else "new"


class AlertSerializer(serializers.ModelSerializer):
    threshold_percent = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    classroom_name = serializers.CharField(source="analysis.classroom.name")
    people = serializers.IntegerField(source="analysis.people")
    capacity = serializers.IntegerField(source="analysis.capacity", allow_null=True)
    created_at = serializers.DateTimeField(source="analysis.created_at")
    job_id = serializers.SerializerMethodField()
    activity = serializers.SerializerMethodField()
    updated_by_name = serializers.CharField(source="updated_by.name", default=None)
    events = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = ["id", "threshold_percent", "status", "classroom_name", "people", "capacity", "created_at",
                  "job_id", "activity", "updated_at", "updated_by_name", "events"]

    def get_status(self, obj):
        return alert_status(obj)

    def get_threshold_percent(self, obj):
        job = getattr(obj.analysis, 'videojob', None)
        return job.options.get('alert_threshold', 100) if job else 100

    def get_job_id(self, obj):
        job = getattr(obj.analysis, "videojob", None)
        return str(job.id) if job else None

    def get_activity(self, obj):
        job = getattr(obj.analysis, "videojob", None)
        return job.get_activity_display() if job else "Sin contexto registrado"

    def get_events(self, obj):
        return [{"status": event.status, "previous_status": event.previous_status,
                 "actor": event.actor.name if event.actor else "Usuario eliminado",
                 "created_at": event.created_at} for event in obj.events.all()]


class AlertStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["new", "review", "resolved"])


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [ReadOrAdmin]
    serializer_class = AlertSerializer
    pagination_class = Pages

    def get_queryset(self):
        qs = Alert.objects.select_related("analysis__classroom", "analysis__videojob", "updated_by").prefetch_related("events__actor").order_by("-analysis__created_at", "-id")
        status = self.request.query_params.get("status")
        if status:
            serializer = AlertStatusSerializer(data={"status": status})
            serializer.is_valid(raise_exception=True)
            qs = qs.filter(resolved=True) if status == "resolved" else qs.filter(resolved=False, in_review=status == "review")
        return qs

    @action(detail=True, methods=["post"], url_path="change-status")
    def change_status(self, request, pk=None):
        data = AlertStatusSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        original = self.get_object()
        with transaction.atomic():
            alert = Alert.objects.select_for_update().get(pk=original.pk)
            previous = alert_status(alert)
            current = data.validated_data["status"]
            if previous != current:
                alert.resolved = current == "resolved"
                alert.in_review = current == "review"
                alert.updated_by = request.user
                alert.updated_at = timezone.now()
                alert.save()
                AlertEvent.objects.create(alert=alert, actor=request.user, previous_status=previous, status=current)
        return Response(AlertSerializer(Alert.objects.select_related("analysis__classroom", "analysis__videojob", "updated_by").get(pk=alert.pk)).data)
