from collections import defaultdict
from django.utils import timezone


def summarize(jobs):
    days, hours = defaultdict(list), defaultdict(list)
    occupancy = []
    over = 0
    for job in jobs:
        people = job.result['people_max']
        stamp = timezone.localtime(job.created_at)
        percent = people / job.capacity_snapshot * 100 if job.capacity_snapshot else None
        if percent is not None:
            occupancy.append(percent)
        if job.capacity_snapshot is not None and people > job.capacity_snapshot:
            over += 1
        days[stamp.date().isoformat()].append((people, percent))
        hours[stamp.hour].append((people, percent))
    def group(key, values):
        rates = [percent for _, percent in values if percent is not None]
        return {'period': key, 'analyses': len(values), 'people_max': max(people for people, _ in values),
                'occupancy_mean': round(sum(rates) / len(rates), 1) if rates else None}
    return {'analyses': len(jobs), 'people_max': max((j.result['people_max'] for j in jobs), default=None),
            'occupancy_mean': round(sum(occupancy) / len(occupancy), 1) if occupancy else None,
            'without_capacity': len(jobs) - len(occupancy), 'over_capacity': over,
            'days': [group(key, values) for key, values in sorted(days.items())],
            'hours': sorted([group(f'{key:02d}:00', values) for key, values in hours.items()],
                            key=lambda g: (-g['people_max'], g['period']))}
