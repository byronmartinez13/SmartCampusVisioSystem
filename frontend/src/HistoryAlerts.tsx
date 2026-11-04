import { useState, type FormEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { api, downloadPdf } from './api';
import { Message } from './components';
import { ReportOverview } from './ReportOverview';
import { dateLabel, errorText, PageHeader, ReadOnlyNotice, ResourceState, useCanManage, useResource } from './campus/shared';
import type { Classroom, Course } from './campus/types';

type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };
type Job = { source: 'video' | 'camera'; id: string; classroom_name: string; original_name: string; activity: string; status: string; created_at: string; capacity_snapshot: number | null; saved_analysis: number | null; result: { people_max: number } | null };
type Alert = { id: number; threshold_percent: number; status: string; classroom_name: string; people: number; capacity: number | null; created_at: string; job_id: string | null; activity: string; events: { status: string; previous_status: string; actor: string; created_at: string }[] };
const states: Record<string, string> = { queued: 'En cola', processing: 'Procesando', completed: 'Completado', failed: 'Fallido', cancelling: 'Cancelando', cancelled: 'Cancelado' };
const activities: Record<string, string> = { class: 'Clase', exam: 'Evaluación', practice: 'Práctica', other: 'Otra' };
const alertStates: Record<string, string> = { new: 'Nueva', review: 'En revisión', resolved: 'Resuelta' };

function Pagination({ data, page, move }: { data: Page<unknown>; page: number; move: (page: number) => void }) {
  return <div className="history-pagination"><span>{data.count} registros · Página {page} de {Math.max(1, Math.ceil(data.count / 20))}</span><button className="button secondary" disabled={!data.previous} onClick={() => move(page - 1)}>Anterior</button><button className="button secondary" disabled={!data.next} onClick={() => move(page + 1)}>Siguiente</button></div>;
}

export function History({ reports = false }: { reports?: boolean }) {
  const [params, setParams] = useSearchParams();
  const resource = useResource<Page<Job>>(`/analysis-history/?${params}`);
  const rooms = useResource<Classroom[]>('/classrooms/');
  const courses = useResource<Course[]>('/courses/');
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState('');
  const page = Number(params.get('page') || 1);
  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = new URLSearchParams();
    new FormData(event.currentTarget).forEach((value, key) => { if (String(value)) next.set(key, String(value)); });
    setParams(next);
  }
  async function download(id: string) {
    setError(''); setDownloading(id);
    try {
      const data = await api(`/video-analyses/${id}/`);
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = `analisis-${id}.json`; anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) { setError(errorText(e)); }
    finally { setDownloading(''); }
  }
  async function pdf(id?: string) {
    setError(''); setDownloading(id || 'report');
    try { await downloadPdf(id ? `/video-analyses/${id}/report/` : `/analysis-history/report/?${params}`, id ? `analisis-${id}.pdf` : 'reporte-ocupacion.pdf'); }
    catch (e) { setError(errorText(e)); }
    finally { setDownloading(''); }
  }
  return <><PageHeader title={reports ? 'Reportes de capacidad y ocupación' : 'Historial de análisis'} subtitle="Consulta resultados y disponibilidad estimada en el momento del análisis." />
    <div className="page-body"><form key={params.toString()} className="panel history-filters" onSubmit={search}><h2>Filtros</h2><div className="filters-row">
      <div className="field"><label htmlFor="history-from">Desde</label><input id="history-from" name="date_from" type="date" defaultValue={params.get('date_from') || ''} /></div>
      <div className="field"><label htmlFor="history-to">Hasta</label><input id="history-to" name="date_to" type="date" defaultValue={params.get('date_to') || ''} /></div>
      <div className="field"><label htmlFor="history-room">Aula</label><select id="history-room" name="classroom" defaultValue={params.get('classroom') || ''}><option value="">Todas las aulas</option>{rooms.data?.map(r => <option key={r.id} value={r.id}>{r.name}{!r.active ? ' (inactiva)' : ''}</option>)}</select></div>
      <div className="field"><label htmlFor="history-activity">Actividad</label><select id="history-activity" name="activity" defaultValue={params.get('activity') || ''}><option value="">Todas</option>{Object.entries(activities).map(([v, label]) => <option key={v} value={v}>{label}</option>)}</select></div>
      <div className="field"><label htmlFor="history-state">Estado</label><select id="history-state" name="status" defaultValue={params.get('status') || ''}><option value="">Todos</option>{Object.entries(states).map(([v, label]) => <option key={v} value={v}>{label}</option>)}</select></div>
      <button className="button primary" type="submit">Buscar</button><button className="button secondary" type="button" onClick={() => setParams({})}>Limpiar filtros</button>
      <div className="field"><label htmlFor="history-course">Curso</label><select id="history-course" name="course" defaultValue={params.get('course') || ''}><option value="">Todos los cursos</option>{courses.data?.map(c => <option key={c.id} value={c.id}>{c.code} - {c.name}</option>)}</select></div>
      <div className="field"><label htmlFor="history-source">Origen</label><select id="history-source" name="source" defaultValue={params.get('source') || ''}><option value="">Todos</option><option value="video">Video grabado</option><option value="camera">Cámara en vivo</option></select></div>
    </div><ResourceState {...rooms} /></form>
    <p className="small-muted">El PDF consolidado incluye solo análisis completados de todas las páginas, hasta 500 registros. Aplica los filtros antes de descargar.</p>
    <button className="button secondary" disabled={!!downloading || resource.loading || !!resource.error} onClick={() => void pdf()}>{downloading === 'report' ? 'Generando PDF…' : 'Descargar reporte consolidado PDF'}</button>
    <Message text={error} /><ResourceState {...resource} />
    {reports && <ReportOverview params={params.toString()} />}
    {resource.data && <section className="panel history-results"><h2>Resultados</h2>
      {resource.data.results.length === 0 ? <p className="inline-empty">No hay análisis que coincidan con los filtros.</p> : <div className="table-wrap"><table><thead><tr><th>Fecha / video</th><th>Aula / actividad</th><th>Estado</th><th>Disponibilidad estimada</th><th>Acciones</th></tr></thead><tbody>{resource.data.results.map(job => {
        const available = job.status === 'completed' && job.result && job.capacity_snapshot !== null ? Math.max(0, job.capacity_snapshot - job.result.people_max) : null;
        return <tr key={job.id}><td>{dateLabel(job.created_at)}<small>{job.original_name}</small></td><td>{job.classroom_name}<small>{activities[job.activity]} · {job.source === 'camera' ? 'Cámara' : 'Video'}</small></td><td>{states[job.status]}<small>{job.saved_analysis ? 'Resumen guardado' : 'Sin guardar resumen'}</small></td><td>{available === null ? 'No disponible' : `${available} puestos`}{job.result && job.capacity_snapshot !== null && job.result.people_max > job.capacity_snapshot && <small>Sobreocupación estimada</small>}</td><td><div className="table-actions">{job.status === 'completed' && <button className="button secondary small" disabled={!!downloading} onClick={() => void pdf(job.id)}>Descargar PDF</button>}<Link className="button secondary small" to={`/analisis/${job.id}`}>Ver análisis</Link><button className="button secondary small" disabled={downloading === job.id} onClick={() => void download(job.id)}>Descargar JSON</button></div></td></tr>;
      })}</tbody></table></div>}
      <Pagination data={resource.data} page={page} move={p => { const next = new URLSearchParams(params); next.set('page', String(p)); setParams(next); }} />
      <p className="small-muted">Disponibilidad estimada: capacidad validada al cargar menos el máximo de personas detectadas, con mínimo cero. No identifica puestos libres concretos ni representa disponibilidad en tiempo real.</p>
    </section>}</div></>;
}

export function Alerts() {
  const [params, setParams] = useSearchParams();
  const resource = useResource<Page<Alert>>(`/alerts/?${params}`);
  const manage = useCanManage();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState<number | null>(null);
  async function change(id: number, status: string) {
    setBusy(id); setError('');
    try { await api(`/alerts/${id}/change-status/`, 'POST', { status }); resource.reload(); }
    catch (e) { setError(errorText(e)); }
    finally { setBusy(null); }
  }
  return <><PageHeader title="Alertas" subtitle="Revisa los casos de sobreocupación registrados al guardar análisis." /><div className="page-body">
    <nav className="academic-tabs alert-tabs" aria-label="Filtrar alertas">{[['', 'Todas'], ['new', 'Nuevas'], ['review', 'En revisión'], ['resolved', 'Resueltas']].map(([value, label]) => <button key={value} className={`button ${params.get('status') === value || (!params.get('status') && !value) ? 'primary' : 'secondary'}`} onClick={() => setParams(value ? { status: value } : {})}>{label}</button>)}</nav>
    {!manage && <ReadOnlyNotice />}<Message text={error} /><ResourceState {...resource} />
    {resource.data?.results.length === 0 && <section className="panel history-results"><p>No hay alertas en este estado.</p></section>}
    {resource.data?.results.map(alert => <article className="panel alert-card" key={alert.id}><div className="alert-title"><AlertTriangle color="#ef4444" /><div><p>{alert.capacity !== null && alert.people > alert.capacity ? 'Sobreocupación detectada' : 'Umbral de ocupación superado'}</p><h2>{alert.classroom_name}</h2></div><span className="record-status">{alertStates[alert.status]}</span></div>
      <p className="small-muted">Umbral configurado al iniciar el análisis: {alert.threshold_percent}% de la capacidad validada.</p>
      <dl className="alert-facts"><div><dt>Ocupación detectada</dt><dd>{alert.people} personas / {alert.capacity ?? 'Sin validar'} puestos</dd></div><div><dt>Fecha</dt><dd>{dateLabel(alert.created_at)}</dd></div><div><dt>Actividad</dt><dd>{alert.activity}</dd></div></dl>
      <div className="alert-actions">{alert.job_id ? <Link to={`/analisis/${alert.job_id}`} className="button secondary">Ver análisis</Link> : <span className="small-muted">Este registro anterior no tiene video vinculado.</span>}
        {manage && <div className="field"><label htmlFor={`alert-${alert.id}`}>Estado de alerta</label><select id={`alert-${alert.id}`} value={alert.status} disabled={busy === alert.id} onChange={e => void change(alert.id, e.target.value)}>{Object.entries(alertStates).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>}
      </div><details><summary>Historial de cambios ({alert.events.length})</summary>{alert.events.length ? <ul>{alert.events.map((event, index) => <li key={index}>{dateLabel(event.created_at)} · {event.actor}: {alertStates[event.previous_status]} → {alertStates[event.status]}</li>)}</ul> : <p className="small-muted">Sin cambios registrados.</p>}</details>
    </article>)}
    {resource.data && <Pagination data={resource.data} page={Number(params.get('page') || 1)} move={page => { const next = new URLSearchParams(params); next.set('page', String(page)); setParams(next); }} />}
    </div></>;
}
