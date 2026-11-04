from datetime import timedelta
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import AssignmentProposal, Course, Classroom
from .serializers import IntervalSerializer, validate_intervals
from . import scheduling_services as service


class SchedulingPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and
                    (request.method in SAFE_METHODS or request.user.is_superuser or request.user.role in ("admin", "coordinator")))


class ProposalInput(serializers.Serializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    classroom = serializers.PrimaryKeyRelatedField(queryset=Classroom.objects.all(), required=False)
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    preferred_kind = serializers.ChoiceField(choices=["", "classroom", "lab"], required=False, default="")
    meetings = IntervalSerializer(many=True, required=False, allow_empty=False)

    def validate_meetings(self, value):
        return [{"weekday": m["weekday"], "start": m["start"].strftime("%H:%M"), "end": m["end"].strftime("%H:%M")}
                for m in validate_intervals(value)]

    def validate(self, data):
        if not 0 <= (data["date_to"] - data["date_from"]).days <= 365:
            raise serializers.ValidationError("El período debe estar ordenado y abarcar como máximo 366 días.")
        return data


class DecisionInput(serializers.Serializer):
    action = serializers.ChoiceField(choices=["accept", "reject", "cancel"])
    note = serializers.CharField(min_length=5, max_length=500)
    classroom = serializers.PrimaryKeyRelatedField(queryset=Classroom.objects.all(), required=False)
    meetings = IntervalSerializer(many=True, required=False, allow_empty=False)
    validate_meetings = ProposalInput.validate_meetings


class ProposalSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)
    creator_name = serializers.CharField(source="creator.name", read_only=True)
    decisions = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentProposal
        fields = ["id", "course", "classroom", "classroom_name", "date_from", "date_to", "meetings",
                  "course_snapshot", "capacity_snapshot", "preferred_kind", "reasons", "status",
                  "creator_name", "created_at", "decisions"]

    def get_decisions(self, obj):
        return [{"action": d.action, "actor": d.actor.name, "note": d.note,
                 "before": d.before, "after": d.after, "created_at": d.created_at} for d in obj.decisions.all()]


class Pages(PageNumberPagination):
    page_size = 20


class ProposalViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [SchedulingPermission]
    serializer_class = ProposalSerializer
    pagination_class = Pages
    queryset = AssignmentProposal.objects.select_related("classroom", "creator").prefetch_related("decisions__actor")

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get("status")
        return qs.filter(status=status) if status else qs

    def create(self, request):
        data = ProposalInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(ProposalSerializer(service.propose(data.validated_data, request.user)).data, status=201)

    @action(detail=False, methods=["get"])
    def alternatives(self, request):
        data = ProposalInput(data=request.query_params)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        course = values["course"]
        return Response(service.alternatives(course, values["date_from"], values["date_to"],
                                             service.slots(course), values["preferred_kind"]))

    @action(detail=True, methods=["post"])
    def decision(self, request, pk=None):
        self.get_object()
        data = DecisionInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(ProposalSerializer(service.decide(pk, data.validated_data, request.user)).data)

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        class Input(serializers.Serializer):
            classroom = serializers.PrimaryKeyRelatedField(queryset=Classroom.objects.all())
            week = serializers.DateField()
        data = Input(data=request.query_params)
        data.is_valid(raise_exception=True)
        day = data.validated_data["week"]
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=6)
        proposals = self.queryset.filter(status="accepted", classroom=data.validated_data["classroom"],
                                        date_from__lte=end, date_to__gte=start)
        sessions = []
        for proposal in proposals:
            for slot in proposal.meetings:
                date = start + timedelta(days=slot["weekday"])
                if proposal.date_from <= date <= proposal.date_to:
                    sessions.append({"proposal": proposal.pk, "date": date, **slot,
                                     "course": proposal.course_snapshot["code"],
                                     "teacher": proposal.course_snapshot["teacher_name"],
                                     "enrollment": proposal.course_snapshot["enrollment"],
                                     "capacity": proposal.capacity_snapshot,
                                     "percent": round(proposal.course_snapshot["enrollment"] / proposal.capacity_snapshot * 100, 1)
                                     if proposal.capacity_snapshot else None})
        return Response({"week_start": start, "sessions": sorted(sessions, key=lambda s: (s["date"], s["start"]))})
