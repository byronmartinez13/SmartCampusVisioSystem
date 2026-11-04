from datetime import timedelta
from django.utils import timezone
from .models import Alert, Analysis, Classroom


def dashboard_summary():
    today = timezone.localdate()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7)
    samples = {start + timedelta(days=i): [] for i in range(7)}
    for analysis in Analysis.objects.filter(created_at__date__gte=start, created_at__date__lt=end):
        if analysis.capacity:
            samples[timezone.localdate(analysis.created_at)].append(100 * analysis.people / analysis.capacity)
    return {
        "classrooms": Classroom.objects.filter(active=True).count(),
        "analyzed_classrooms": Analysis.objects.values("classroom_id").distinct().count(),
        "open_alerts": Alert.objects.filter(resolved=False).count(),
        "week_start": start.isoformat(),
        "occupancy": [
            {"date": day.isoformat(), "percent": round(sum(values) / len(values), 1) if values else None}
            for day, values in samples.items()
        ],
    }
