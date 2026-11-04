from rest_framework import serializers
from .models import Classroom, ClassroomAvailability, CapacityValidation, Course, CourseMeeting, Subject, Teacher


class EquipmentField(serializers.ListField):
    child = serializers.CharField(max_length=80)

    def __init__(self, **kwargs):
        super().__init__(max_length=30, **kwargs)

    def to_internal_value(self, data):
        values = super().to_internal_value(data)
        return list(dict.fromkeys(value.strip().lower() for value in values))


class UniqueNormalizedMixin:
    """Early user-friendly validation, backed by database uniqueness constraints."""
    unique_field = "name"

    def validate(self, attrs):
        attrs = super().validate(attrs)
        field = self.unique_field
        if field in attrs:
            value = attrs[field].strip()
            if field == "email":
                value = value.lower()
            if field == "code":
                value = value.upper()
            attrs[field] = value
            query = self.Meta.model.objects.filter(**{f"{field}__iexact": value})
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError({field: "Ya existe un registro con este valor."})
        return attrs


class IntervalSerializer(serializers.Serializer):
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    start = serializers.TimeField(format="%H:%M", input_formats=["%H:%M", "%H:%M:%S"])
    end = serializers.TimeField(format="%H:%M", input_formats=["%H:%M", "%H:%M:%S"])

    def validate(self, attrs):
        if any(attrs[key].second or attrs[key].microsecond for key in ("start", "end")):
            raise serializers.ValidationError("Las franjas deben expresarse en minutos completos.")
        if attrs["end"] <= attrs["start"]:
            raise serializers.ValidationError("La hora final debe ser posterior a la inicial, en el mismo día.")
        return attrs


def validate_intervals(intervals):
    ordered = sorted(intervals, key=lambda value: (value["weekday"], value["start"]))
    for previous, current in zip(ordered, ordered[1:]):
        if previous["weekday"] == current["weekday"] and previous["end"] > current["start"]:
            raise serializers.ValidationError("Hay franjas horarias superpuestas.")
    return ordered


class CapacityValidationSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.name", read_only=True, default="Usuario no disponible")

    class Meta:
        model = CapacityValidation
        fields = ["id", "value", "note", "actor_name", "created_at"]


class CapacityInputSerializer(serializers.Serializer):
    value = serializers.IntegerField(min_value=0, max_value=10000)
    note = serializers.CharField(max_length=500, min_length=5)


class ClassroomSerializer(UniqueNormalizedMixin, serializers.ModelSerializer):
    equipment = EquipmentField(required=False)
    availability = IntervalSerializer(many=True, required=False)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    camera_display = serializers.CharField(source="get_camera_display", read_only=True)
    validated_by_name = serializers.SerializerMethodField()
    capacity = serializers.IntegerField(min_value=0, max_value=10000, allow_null=True, required=False)

    class Meta:
        model = Classroom
        fields = ["id", "name", "kind", "kind_label", "location", "capacity", "active", "equipment",
                  "camera", "camera_label", "camera_display", "availability", "validated_capacity",
                  "capacity_validated_at", "validated_by_name"]
        read_only_fields = ["validated_capacity", "capacity_validated_at"]

    def validate_availability(self, value):
        return validate_intervals(value)

    def get_validated_by_name(self, obj):
        return obj.capacity_validated_by.name if obj.capacity_validated_by else None


class TeacherSerializer(UniqueNormalizedMixin, serializers.ModelSerializer):
    unique_field = "email"

    class Meta:
        model = Teacher
        fields = ["id", "name", "email", "active"]


class SubjectSerializer(UniqueNormalizedMixin, serializers.ModelSerializer):
    unique_field = "code"

    class Meta:
        model = Subject
        fields = ["id", "code", "name", "active"]


class CourseSerializer(UniqueNormalizedMixin, serializers.ModelSerializer):
    unique_field = "code"
    required_equipment = EquipmentField(required=False)
    meetings = IntervalSerializer(many=True, required=False)
    teacher_name = serializers.CharField(source="teacher.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    enrollment = serializers.IntegerField(min_value=0, max_value=10000)

    class Meta:
        model = Course
        fields = ["id", "code", "name", "subject", "subject_name", "teacher", "teacher_name",
                  "enrollment", "active", "required_equipment", "meetings"]

    def validate_meetings(self, value):
        return validate_intervals(value)
