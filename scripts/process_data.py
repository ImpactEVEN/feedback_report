"""Allowlisted, aggregate-only output. Never serialize original submissions."""
from collections import defaultdict
from datetime import date, datetime, timezone
import math

FIELDS = {'hr': 'Trip coordination (HR)', 'education': 'Preparation & materials (Education)', 'logistics': 'Preparation (Logistics)',
          'im': 'Preparation (IM)', 'sm': 'Preparation (SM)', 'acompa': 'Team accompaniment',
          'estadia': 'Accommodation', 'comidas': 'Meals', 'vuelos': 'Flight arrangements'}
SUPPORT = list(FIELDS)[:5]
TRIP = list(FIELDS)[5:]

def field(record, name):
    if name in record:
        return record[name]
    matches = [v for k, v in record.items() if k.rsplit('/', 1)[-1] == name]
    if len(matches) > 1:
        raise ValueError('Ambiguous form field: ' + name)
    return matches[0] if matches else None

def rating(value):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
        return int(n) if math.isfinite(n) and n.is_integer() and 1 <= n <= 5 else None
    except (TypeError, ValueError):
        return None

def trip_date(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError:
        return None

def aggregate(records, min_responses=2, demo=False):
    if min_responses < 2:
        raise ValueError('Minimum group size must be at least 2')
    groups = defaultdict(list)
    seen = set()
    invalid = 0
    for row in records:
        identity = row.get('_uuid') or row.get('_id')
        if identity is not None:
            if str(identity) in seen:
                continue
            seen.add(str(identity))
        day = trip_date(field(row, 'viaje'))
        if day is None:
            invalid += 1
            continue
        clean = {k: rating(field(row, k)) for k in FIELDS}
        clean['comments'] = [{'category': k, 'text': field(row, k).strip()} for k in ['pre_feedback', 'feedback', 'apoyo', 'header_3'] if isinstance(field(row, k), str) and field(row, k).strip()]
        groups[day].append(clean)
    buckets = []
    withheld = 0
    for day, rows in sorted(groups.items()):
        if len(rows) < min_responses:
            withheld += len(rows)
            continue
        metrics = {}
        for k in FIELDS:
            values = [r[k] for r in rows if r[k] is not None]
            # Each question also needs enough valid answers before publication.
            metrics[k] = {'counts': [values.count(i) for i in range(1, 6)]} if len(values) >= min_responses else {'counts': None}
        composites = {}
        for name, keys in [('support', SUPPORT), ('trip', TRIP)]:
            # Complete cases keep each respondent equally weighted.
            values = [sum(r[k] for k in keys) / len(keys) for r in rows if all(r[k] is not None for k in keys)]
            composites[name] = {'sum': sum(values), 'n': len(values)} if len(values) >= min_responses else {'sum': None, 'n': None}
        buckets.append({'date': day, 'responses': len(rows), 'metrics': metrics, 'composites': composites, 'comments': [c for row in rows for c in row['comments']] if not demo else []})
    return {'schema_version': 1, 'updated_at': datetime.now(timezone.utc).isoformat(),
            'demo': demo, 'minimum_group_size': min_responses,
            'withheld_responses': withheld, 'invalid_date_responses': invalid,
            'fields': FIELDS, 'support_fields': SUPPORT, 'trip_fields': TRIP,
            'buckets': buckets}
