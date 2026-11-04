from pathlib import Path
from rest_framework import serializers
from campus.models import Classroom, Course
from .models import VideoJob


class UploadSerializer(serializers.ModelSerializer):
    classroom = serializers.PrimaryKeyRelatedField(queryset=Classroom.objects.filter(active=True))
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.filter(active=True), required=False, allow_null=True)
    confidence = serializers.FloatField(min_value=.1, max_value=.95, required=False)

    class Meta:
        model = VideoJob
        fields = ["classroom", "course", "activity", "confidence", "video"]

    def validate_video(self, value):
        if not 0 < value.size <= 250 * 1024 * 1024:
            raise serializers.ValidationError("Selecciona un video de hasta 250 MB.")
        extension = Path(value.name).suffix.lower()
        header = value.read(12)
        value.seek(0)
        if not ((extension == ".mp4" and header[4:8] == b"ftyp")
                or (extension == ".avi" and header[:4] == b"RIFF" and header[8:12] == b"AVI ")):
            raise serializers.ValidationError("Se requiere un archivo MP4 o AVI válido.")
        return value


class JobSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)
    course_name = serializers.CharField(source="course.name", default=None, read_only=True)
    creator_name = serializers.CharField(source="creator.name", read_only=True)

    class Meta:
        model = VideoJob
        fields = ["id", "source", "options", "classroom", "classroom_name", "course", "course_name", "creator_name",
                  "activity", "original_name", "confidence", "capacity_snapshot", "status",
                  "progress", "error", "result", "saved_analysis", "created_at", "updated_at"]
        read_only_fields = fields
