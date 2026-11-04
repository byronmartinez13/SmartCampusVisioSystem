from django.db import transaction
from rest_framework import serializers, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsAdministrator
from .models import SystemSettings, AssignmentRule, AdministrativeEvent
from .permissions import ReadOrAdmin
from .scheduling_services import lock_schedule, validate_assignments


SETTING_FIELDS = ['confidence', 'auto_save', 'auto_pdf', 'record_live', 'alerts_enabled', 'alert_threshold', 'date_format', 'version']


def analysis_options():
    obj = SystemSettings.objects.filter(pk=1).first() or SystemSettings()
    return {field: getattr(obj, field) for field in SETTING_FIELDS if field != 'version'}


class SettingsSerializer(serializers.ModelSerializer):
    confidence = serializers.FloatField(min_value=.1, max_value=.95)
    alert_threshold = serializers.IntegerField(min_value=1, max_value=200)
    date_format = serializers.ChoiceField(choices=['dmy', 'ymd'])
    class Meta:
        model = SystemSettings
        fields = SETTING_FIELDS


class SettingsView(APIView):
    permission_classes = [ReadOrAdmin]

    def get(self, request):
        obj = SystemSettings.objects.filter(pk=1).first() or SystemSettings(pk=1)
        return Response(SettingsSerializer(obj).data)

    @transaction.atomic
    def patch(self, request):
        lock_schedule()
        obj, _ = SystemSettings.objects.get_or_create(pk=1)
        if request.data.get('version') != obj.version:
            raise serializers.ValidationError('La configuración cambió. Recarga antes de guardar.')
        before = SettingsSerializer(obj).data
        data = SettingsSerializer(obj, data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        obj = data.save(version=obj.version + 1)
        AdministrativeEvent.objects.create(actor=request.user, action='settings.updated', target='system',
                                           before=before, after=SettingsSerializer(obj).data)
        return Response(SettingsSerializer(obj).data)


class RuleSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source='get_kind_display', read_only=True)
    class Meta:
        model = AssignmentRule
        fields = ['id', 'kind', 'label', 'value', 'active', 'version']

    def validate(self, data):
        kind = data.get('kind', self.instance.kind if self.instance else None)
        value = data.get('value', self.instance.value if self.instance else '')
        if self.instance and kind != self.instance.kind:
            raise serializers.ValidationError('El tipo no se puede cambiar. Edita su valor o desactiva la regla.')
        if kind in ('min_spare', 'max_enrollment'):
            if not value.isascii() or not value.isdigit() or not 1 <= int(value) <= 1000:
                raise serializers.ValidationError('El valor debe ser un entero entre 1 y 1000.')
            data['value'] = str(int(value))
        elif kind == 'preferred_kind' and value not in ('classroom', 'lab'):
            raise serializers.ValidationError('La preferencia debe ser classroom o lab.')
        elif kind == 'extra_equipment' and (not value.strip() or ',' in value):
            raise serializers.ValidationError('Indica un equipo del catálogo, sin comas.')
        if kind == 'extra_equipment':
            data['value'] = value.strip()
        return data


class RuleViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOrAdmin]
    serializer_class = RuleSerializer
    queryset = AssignmentRule.objects.order_by('kind')
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        lock_schedule()
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        lock_schedule()
        obj = self.get_object()
        if request.data.get('version') != obj.version:
            raise serializers.ValidationError('La regla cambió. Actualiza la lista.')
        return super().partial_update(request, *args, **kwargs)

    def perform_create(self, serializer):
        obj = serializer.save(version=1)
        validate_assignments()
        AdministrativeEvent.objects.create(actor=self.request.user, action='rule.created', target=str(obj.pk),
                                           after=RuleSerializer(obj).data)

    def perform_update(self, serializer):
        before = RuleSerializer(serializer.instance).data.copy()
        obj = serializer.save(version=serializer.instance.version + 1)
        validate_assignments()
        AdministrativeEvent.objects.create(actor=self.request.user, action='rule.updated', target=str(obj.pk),
                                           before=before, after=RuleSerializer(obj).data)


class AuditView(APIView):
    permission_classes = [IsAdministrator]
    def get(self, request):
        return Response([{'id': e.pk, 'actor': e.actor.name, 'action': e.action, 'target': e.target,
                          'before': e.before, 'after': e.after, 'created_at': e.created_at}
                         for e in AdministrativeEvent.objects.select_related('actor').order_by('-pk')[:100]])
