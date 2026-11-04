from django.db import IntegrityError, transaction
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from . import management_services as services
from .models import Classroom, Course, Teacher, Subject
from .permissions import ReadOrAdmin
from .serializers import (
    ClassroomSerializer, CourseSerializer, TeacherSerializer, SubjectSerializer,
    CapacityInputSerializer, CapacityValidationSerializer,
)


class ManagedViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [ReadOrAdmin]
    filter_backends = [SearchFilter]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        query = super().get_queryset()
        active = self.request.query_params.get("active")
        if active in ("true", "false"):
            query = query.filter(active=active == "true")
        return query

    def persist(self, serializer):
        return services.save_catalog(serializer)

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.instance = self.persist(serializer)
        except IntegrityError as exc:
            raise ValidationError("No se pudo guardar: ya existe un registro con esos datos.") from exc

    def perform_update(self, serializer):
        self.perform_create(serializer)


class ClassroomViewSet(ManagedViewSet):
    queryset = Classroom.objects.select_related("capacity_validated_by").prefetch_related("availability").order_by("name", "pk")
    serializer_class = ClassroomSerializer
    search_fields = ["name", "location"]

    def get_queryset(self):
        query = super().get_queryset()
        kind = self.request.query_params.get("kind")
        return query.filter(kind=kind) if kind in ("classroom", "lab") else query

    def persist(self, serializer):
        return services.save_classroom(dict(serializer.validated_data), serializer.instance)

    @action(detail=True, methods=["post"], url_path="validate-capacity")
    def validate_capacity(self, request, pk=None):
        classroom = self.get_object()
        serializer = CapacityInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = services.validate_capacity(classroom.pk, serializer.validated_data, request.user)
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["get"])
    def validations(self, request, pk=None):
        records = self.get_object().validations.select_related("actor").order_by("-created_at", "-pk")
        return Response(CapacityValidationSerializer(records, many=True).data)

    @action(detail=True, methods=["get"])
    def activity(self, request, pk=None):
        # Actual persisted summaries only. Full analysis detail is part of the vision milestone.
        rows = self.get_object().analysis_set.order_by("-created_at")[:20]
        return Response([{"id": row.pk, "created_at": row.created_at, "people": row.people,
                          "capacity": row.capacity,
                          "occupancy": round(row.people / row.capacity * 100, 1) if row.capacity else None}
                         for row in rows])


class TeacherViewSet(ManagedViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    search_fields = ["name", "email"]


class SubjectViewSet(ManagedViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    search_fields = ["code", "name"]


class CourseViewSet(ManagedViewSet):
    queryset = Course.objects.select_related("teacher", "subject").prefetch_related("meetings").all()
    serializer_class = CourseSerializer
    search_fields = ["code", "name", "teacher__name", "subject__name"]

    def persist(self, serializer):
        return services.save_course(dict(serializer.validated_data), serializer.instance)
