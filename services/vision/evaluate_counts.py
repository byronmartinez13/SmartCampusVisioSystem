"""Compare exported detector samples with explicit human counts; never invent labels."""
import argparse
import json
from pathlib import Path


def evaluate(export, annotations):
    result = export.get('result', export)
    samples = result.get('samples', [])
    predicted = {s['frame']: s['people'] for s in samples}
    labels = annotations.get('samples', [])
    if not labels:
        raise ValueError('Se requiere al menos un fotograma con conteo humano.')
    if annotations.get('analysis_id') and str(export.get('id')) != str(annotations['analysis_id']):
        raise ValueError('Las anotaciones corresponden a otro análisis.')
    seen, rows = set(), []
    for label in labels:
        frame, people = label.get('frame'), label.get('people')
        if type(frame) is not int or type(people) is not int or min(frame, people) < 0:
            raise ValueError('frame y people deben ser enteros no negativos.')
        if frame in seen or frame not in predicted:
            raise ValueError('Hay fotogramas duplicados o que no existen en el resultado.')
        seen.add(frame)
        error = predicted[frame] - people
        rows.append({'frame': frame, 'human': people, 'detected': predicted[frame], 'error': error, 'absolute_error': abs(error)})
    maximum = max(r['absolute_error'] for r in rows)
    return {'scope': 'Solo fotogramas anotados; no acredita precisión en otros videos o aulas.',
            'model': result.get('detector'), 'annotated_frames': len(rows), 'sampled_frames': len(samples),
            'mean_absolute_error': round(sum(r['absolute_error'] for r in rows) / len(rows), 3),
            'max_absolute_error': maximum, 'frames_outside_plus_minus_2': sum(r['absolute_error'] > 2 for r in rows),
            'within_plus_minus_2_on_annotated_frames': maximum <= 2, 'comparison': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    parser.add_argument('annotations', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(json.loads(args.export.read_text(encoding='utf-8')), json.loads(args.annotations.read_text(encoding='utf-8')))
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Fotogramas: {report['annotated_frames']}; error absoluto máximo: {report['max_absolute_error']}; fuera de ±2: {report['frames_outside_plus_minus_2']}")
