"""PDF reports generated only from persisted analysis results."""
from io import BytesIO
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether


def report_pdf(jobs, *, filters=None, individual=False):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles['Normal'].fontSize = 9
    styles['Normal'].leading = 13
    styles['Heading1'].keepWithNext = True
    styles['Heading2'].keepWithNext = True

    def p(value, style='Normal'):
        return Paragraph(escape(str(value if value is not None else 'No disponible')).replace('\n', '<br/>'), styles[style])

    def table(rows, widths):
        item = Table([[p(cell) for cell in row] for row in rows], colWidths=widths, repeatRows=1, hAlign='LEFT')
        item.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7eef6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, -1), .4, colors.HexColor('#d7e0eb')),
        ]))
        return item

    story = [p('Smart Campus Vision', 'Title'), p('Reporte de capacidad y ocupación', 'Heading1'),
             p('Emitido: ' + timezone.localtime().strftime('%d/%m/%Y %H:%M %Z')),
             p('Fuente: análisis de video y muestras de cámara. La ocupación es una estimación histórica, no información en vivo.'), Spacer(1, .4 * cm)]
    if filters:
        labels = {'classroom': 'ID de aula', 'course': 'ID de curso', 'date_from': 'Desde', 'date_to': 'Hasta', 'activity': 'Actividad', 'status': 'Estado', 'source': 'Origen'}
        story += [p('Filtros aplicados', 'Heading2')]
        story += [p(f'{labels[key]}: {value}') for key, value in filters.items() if key in labels and value]
    story += [p(f'Análisis incluidos: {len(jobs)}')]
    if individual:
        job = jobs[0]
        result = job.result
        detector = result.get('detector') or {}
        reference = {'monitors': 'Monitores', 'chairs': 'Sillas', 'workstations': 'Puestos de trabajo'}.get(detector.get('seat_semantics'), 'Objetos de referencia')
        capacity = job.capacity_snapshot
        people = result['people_max']
        rows = [ ['Dato', 'Valor'], ['Identificador', job.pk], ['Origen', job.get_source_display()], ['Aula (nombre actual)', job.classroom.name],
                ['Curso (nombre actual)', job.course.name if job.course else 'Sin curso'],
                ['Fecha de carga', timezone.localtime(job.created_at).strftime('%d/%m/%Y %H:%M %Z')],
                ['Actividad', job.get_activity_display()], ['Archivo', job.original_name],
                ['Resumen guardado', 'Sí' if job.saved_analysis_id else 'No'],
                ['Capacidad validada al cargar', capacity], ['Personas (máximo detectado)', people],
                ['Personas (promedio)', result.get('people_mean')],
                [reference + ' (máximo detectado)', result.get('seats_max')],
                ['Ocupación estimada', f'{people / capacity * 100:.1f} %' if capacity else 'No disponible'],
                ['Disponibilidad estimada', max(0, capacity - people) if capacity is not None else None],
                ['Modelo', detector.get('model')], ['SHA256 del modelo', detector.get('sha256')],
                ['Umbral de confianza', job.confidence], ['Fotogramas evaluados', result.get('sampled_frames')]]
        story += [table(rows, [6 * cm, 11 * cm])]
    else:
        from .reporting import summarize
        summary = summarize(jobs)
        story += [p('Resumen del período', 'Heading2'),
                  p(f"Máximo de personas en un análisis: {summary['people_max'] if jobs else 'No disponible'}. Análisis sobre capacidad: {summary['over_capacity']}. Sin capacidad positiva: {summary['without_capacity']}."),
                  p(f"Ocupación media de los análisis con capacidad positiva: {summary['occupancy_mean'] if summary['occupancy_mean'] is not None else 'No disponible'} %.")]
        if summary['days']:
            story += [p('Evolución por fecha de carga o inicio', 'Heading2'), table([
                ['Fecha', 'Análisis', 'Personas máx.', 'Ocupación media (%)']] + [
                    [g['period'], g['analyses'], g['people_max'], g['occupancy_mean']] for g in summary['days']],
                [5 * cm, 3 * cm, 4 * cm, 5 * cm])]
            story += [p('Horas con mayor máximo observado', 'Heading2'), table([
                ['Hora de carga/inicio', 'Análisis', 'Personas máx.']] + [
                    [g['period'], g['analyses'], g['people_max']] for g in summary['hours'][:5]], [7 * cm, 5 * cm, 5 * cm]),
                p('Las horas corresponden a la carga del archivo o al inicio de cámara en America/Guayaquil. No acreditan la hora de grabación del video. No se suman conteos como personas únicas.'), Spacer(1, .4 * cm)]
        story += [p('Detalle de análisis', 'Heading2')]
        rows = [['Fecha / ID', 'Aula actual / actividad', 'Personas máx.', 'Capacidad al cargar', 'Ocupación']]
        for job in jobs:
            people = job.result['people_max']
            capacity = job.capacity_snapshot
            rows.append([timezone.localtime(job.created_at).strftime('%d/%m/%Y %H:%M') + '\n' + str(job.pk),
                         job.classroom.name + ' / ' + job.get_activity_display() + ' / ' + job.get_source_display(), people, capacity,
                         f'{people / capacity * 100:.1f} %' if capacity else 'No disponible'])
        story += [table(rows, [5 * cm, 5 * cm, 2 * cm, 2.5 * cm, 2.5 * cm])] if jobs else [p('No hay análisis completados con estos filtros.')]
    story += [Spacer(1, .4 * cm), KeepTogether([p('Interpretación y límites', 'Heading2'),
              p('Se utiliza el máximo de personas detectadas, no personas únicas. Los máximos de personas y objetos pueden corresponder a fotogramas distintos. Los monitores y sillas detectados no acreditan puestos utilizables ni sustituyen la capacidad validada.'),
              p('La confianza del detector no mide precisión. El error frente a conteos humanos sigue pendiente de validación. Una sobreocupación estimada requiere revisión. La capacidad corresponde a la instantánea al cargar; los nombres del catálogo son actuales.')])]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#536477'))
        canvas.drawString(1.8 * cm, 1.1 * cm, 'Smart Campus Vision | Uso institucional')
        canvas.drawRightString(19.2 * cm, 1.1 * cm, f'Página {doc.page}')
        canvas.restoreState()

    SimpleDocTemplate(buffer, title='Reporte de capacidad y ocupación', author='Smart Campus Vision',
                      leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm,
                      bottomMargin=1.8 * cm).build(story, onFirstPage=footer, onLaterPages=footer)
    filename = f'analisis-{jobs[0].pk}.pdf' if individual else 'reporte-ocupacion.pdf'
    return HttpResponse(buffer.getvalue(), content_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="{filename}"', 'Cache-Control': 'private, no-store',
        'X-Content-Type-Options': 'nosniff'})
