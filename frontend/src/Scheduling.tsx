import { useState, type FormEvent } from 'react';
import { Link, NavLink, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { api } from './api';
import { useAuth } from './auth';
import { Message } from './components';
import { days, dateLabel, errorText, IntervalEditor, IntervalList, PageHeader, ResourceState, useResource } from './campus/shared';
import type { Classroom, Course, Interval } from './campus/types';

type Proposal = { id: number; course: number; classroom: number; classroom_name: string; date_from: string; date_to: string; meetings: Interval[]; capacity_snapshot: number; preferred_kind: string; reasons: string[]; status: string; creator_name: string; created_at: string;
  course_snapshot: { code: string; name: string; teacher_name: string; enrollment: number; required_equipment: string[] };
  decisions: { action: string; actor: string; note: string; created_at: string; before: { classroom: number; meetings: Interval[] }; after: { classroom: number; meetings: Interval[] } }[] };
type Options = { candidates: { classroom: number; name: string; capacity: number; spare: number; reasons: string[] }[]; excluded: { classroom: number; name: string; reasons: string[] }[] };
const statuses: Record<string, string> = { pending: 'Pendiente', accepted: 'Aceptada', rejected: 'Rechazada', cancelled: 'Cancelada' };
const actions: Record<string, string> = { accept: 'Aceptar', reject: 'Rechazar', cancel: 'Cancelar asignación' };
function useScheduler() { const { user } = useAuth(); return user?.role === 'admin' || user?.role === 'coordinator'; }
function Tabs() { return <nav className="academic-tabs"><NavLink end to="/horarios">Vista semanal</NavLink><NavLink to="/horarios/propuestas">Propuestas y decisiones</NavLink><NavLink to="/horarios/nueva">Consultar alternativas</NavLink><NavLink to="/administracion/reglas">Reglas</NavLink></nav>; }
function today() { const d = new Date(); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); }

export function Schedule() {
  const rooms = useResource<Classroom[]>('/classrooms/');
  const [params, setParams] = useSearchParams();
  const room = params.get('classroom') || '';
  const week = params.get('week') || today();
  return <><PageHeader title="Horarios" subtitle="Asignaciones académicas y ocupación planificada por matrícula." /><div className="page-body"><Tabs />
    <section className="panel detail-panel"><div className="form-grid"><div className="field"><label htmlFor="calendar-room">Aula / laboratorio</label><select id="calendar-room" value={room} onChange={e => setParams({ classroom: e.target.value, week })}><option value="">Selecciona un aula</option>{rooms.data?.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select></div><div className="field"><label htmlFor="calendar-week">Semana que contiene el día</label><input id="calendar-week" type="date" value={week} onChange={e => { if (e.target.value) setParams({ classroom: room, week: e.target.value }); }} /></div></div><ResourceState {...rooms} /></section>
    {room ? <CalendarBoard room={room} week={week} /> : <p className="inline-empty">Selecciona un aula para consultar sus asignaciones.</p>}
    <section className="panel detail-panel"><h2>Reglas de asignación</h2><p className="small-muted">Se exige capacidad validada suficiente, equipamiento requerido, disponibilidad declarada y ausencia de cruces de aula, docente y curso. Sin disponibilidad declarada, el aula no se ofrece. Las alternativas se ordenan por preferencia de tipo y menor cantidad de puestos sobrantes.</p><p className="inline-empty"><Link to="/aulas">Configurar aulas y disponibilidad</Link> · <Link to="/academico/cursos">Configurar cursos y franjas</Link></p></section>
  </div></>;
}

function CalendarBoard({ room, week }: { room: string; week: string }) {
  type Session = { proposal: number; date: string; weekday: number; start: string; end: string; course: string; teacher: string; enrollment: number; capacity: number; percent: number | null };
  const resource = useResource<{ week_start: string; sessions: Session[] }>('/assignments/calendar/?' + new URLSearchParams({ classroom: room, week }));
  const sessions = resource.data?.sessions || [];
  const intervals = [...new Set(sessions.map(s => s.start + '–' + s.end))].sort();
  return <section className="panel detail-panel schedule-board"><h2>Ocupación semanal planificada</h2><ResourceState {...resource} />
    {resource.data && <><p className="small-muted">Semana desde {resource.data.week_start}. Porcentaje = matrícula / capacidad validada al aceptar. No es ocupación detectada por cámara.</p>
      {!sessions.length ? <p className="inline-empty">No hay asignaciones aceptadas para esta aula y semana.</p> : <div className="table-wrap"><table><thead><tr><th>Franja</th>{days.map(d => <th key={d}>{d}</th>)}</tr></thead><tbody>{intervals.map(interval => <tr key={interval}><th>{interval}</th>{days.map((day, i) => <td key={day}>{sessions.filter(s => s.weekday === i && s.start + '–' + s.end === interval).map(s => <Link key={s.proposal} className={'schedule-cell ' + (s.percent !== null && s.percent >= 90 ? 'high' : s.percent !== null && s.percent >= 70 ? 'medium' : 'low')} to={'/horarios/propuestas/' + s.proposal}><strong>{s.percent === null ? 'Sin capacidad' : s.percent + '%'}</strong><span>{s.course}</span><small>{s.enrollment} / {s.capacity} puestos</small><small>{s.teacher}</small></Link>)}{!sessions.some(s => s.weekday === i && s.start + '–' + s.end === interval) && <span className="small-muted">Sin asignación</span>}</td>)}</tr>)}</tbody></table></div>}
      <p className="inline-empty">{sessions.some(s => (s.percent ?? 0) >= 90) ? 'Hay sesiones planificadas al 90% o más de capacidad. Revisa las alternativas antes de aumentar la matrícula.' : sessions.length ? 'Las sesiones planificadas están por debajo del 90% de capacidad.' : 'Consulta alternativas para crear una propuesta.'} Un espacio sin asignación no garantiza disponibilidad fuera de sus franjas declaradas.</p>
    </>}
  </section>;
}

export function Proposals() {
  const [params, setParams] = useSearchParams();
  const resource = useResource<{ results: Proposal[]; count: number; next: string | null; previous: string | null }>('/assignments/?' + params);
  const page = Number(params.get('page') || 1);
  return <><PageHeader title="Propuestas y decisiones" subtitle="Recomendaciones pendientes, asignaciones aceptadas e historial de decisiones." /><div className="page-body"><Tabs /><div className="field"><label htmlFor="proposal-state">Estado de propuesta</label><select id="proposal-state" value={params.get('status') || ''} onChange={e => setParams(e.target.value ? { status: e.target.value } : {})}><option value="">Todos</option>{Object.entries(statuses).map(([v, label]) => <option key={v} value={v}>{label}</option>)}</select></div><ResourceState {...resource} />
    {resource.data && <section className="panel detail-panel">{resource.data.results.length ? <div className="table-wrap"><table><thead><tr><th>Curso / docente</th><th>Aula / período</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{resource.data.results.map(p => <tr key={p.id}><td>{p.course_snapshot.code} · {p.course_snapshot.name}<small>{p.course_snapshot.teacher_name}</small></td><td>{p.classroom_name}<small>{p.date_from} a {p.date_to}</small></td><td>{statuses[p.status]}</td><td><Link className="button secondary small" to={'/horarios/propuestas/' + p.id}>Ver propuesta #{p.id}</Link></td></tr>)}</tbody></table></div> : <p>No hay propuestas en este estado.</p>}
      <div className="history-pagination"><span>{resource.data.count} propuestas · Página {page}</span>{[[-1, 'Anterior'], [1, 'Siguiente']].map(([delta, label]) => <button key={label} className="button secondary" disabled={delta === -1 ? !resource.data?.previous : !resource.data?.next} onClick={() => { const next = new URLSearchParams(params); next.set('page', String(page + Number(delta))); setParams(next); }}>{label}</button>)}</div></section>}
  </div></>;
}

export function NewProposal() {
  const courses = useResource<Course[]>('/courses/?active=true');
  const [values, setValues] = useState({ course: '', date_from: today(), date_to: today(), preferred_kind: '' });
  const [options, setOptions] = useState<Options | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const manage = useScheduler();
  const navigate = useNavigate();
  const course = courses.data?.find(c => String(c.id) === values.course);
  function update(key: keyof typeof values, value: string) { setValues(v => ({ ...v, [key]: value })); setOptions(null); setError(''); }
  async function search(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(''); setOptions(null);
    try { setOptions(await api<Options>('/assignments/alternatives/?' + new URLSearchParams(values))); }
    catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  async function create(classroom: number) {
    setBusy(true); setError('');
    try { const p = await api<Proposal>('/assignments/', 'POST', { ...values, course: Number(values.course), classroom }); navigate('/horarios/propuestas/' + p.id); }
    catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <><PageHeader title="Consultar alternativas" subtitle="Genera una propuesta para revisión; no reserva el aula automáticamente." /><div className="page-body"><Tabs /><ResourceState {...courses} />
    <form className="panel entity-form" onSubmit={search}><fieldset disabled={busy}><div className="field"><label htmlFor="proposal-course">Curso</label><select id="proposal-course" required value={values.course} onChange={e => update('course', e.target.value)}><option value="">Selecciona un curso</option>{courses.data?.map(c => <option key={c.id} value={c.id}>{c.code} · {c.name}</option>)}</select></div>
      <div className="form-grid"><div className="field"><label htmlFor="proposal-from">Inicio del período</label><input id="proposal-from" type="date" required value={values.date_from} onChange={e => update('date_from', e.target.value)} /></div><div className="field"><label htmlFor="proposal-to">Fin del período</label><input id="proposal-to" type="date" required min={values.date_from} value={values.date_to} onChange={e => update('date_to', e.target.value)} /></div></div>
      <div className="field"><label htmlFor="proposal-preference">Preferencia de espacio (opcional)</label><select id="proposal-preference" value={values.preferred_kind} onChange={e => update('preferred_kind', e.target.value)}><option value="">Sin preferencia</option><option value="lab">Priorizar laboratorios</option><option value="classroom">Priorizar aulas</option></select></div>
      {course && <><p className="inline-empty">{course.enrollment} estudiantes · {course.teacher_name} · Equipamiento: {course.required_equipment.join(', ') || 'Sin requisitos'}</p><IntervalList value={course.meetings} /></>}
      <p className="inline-empty">Se utilizan las franjas semanales del curso. La preferencia ordena las alternativas, pero nunca permite incumplir una restricción obligatoria.</p><button className="button primary" disabled={busy || !values.course}>Buscar alternativas</button>
    </fieldset></form><Message text={error} />
    {options && <><section className="panel detail-panel schedule-options"><h2>Alternativas compatibles ({options.candidates.length})</h2>{!options.candidates.length && <p>No hay alternativas compatibles. Revisa los motivos de exclusión y los datos del curso.</p>}{options.candidates.map((room, index) => <article key={room.classroom}><h3>{room.name} {index === 0 && <span className="record-status is-active">Primera opción</span>}</h3><p>{room.capacity} puestos validados · {room.spare} puestos sobrantes según matrícula</p><ul>{room.reasons.map(r => <li key={r}>{r}</li>)}</ul>{manage && <button className="button primary" disabled={busy} onClick={() => void create(room.classroom)}>Crear propuesta para {room.name}</button>}</article>)}</section>
      <section className="panel detail-panel"><h2>Espacios excluidos ({options.excluded.length})</h2>{options.excluded.map(room => <details key={room.classroom}><summary>{room.name}</summary><ul>{room.reasons.map(r => <li key={r}>{r}</li>)}</ul></details>)}</section></>}
  </div></>;
}

export function ProposalDetail() {
  const { id } = useParams();
  const resource = useResource<Proposal>('/assignments/' + id + '/');
  return <><PageHeader title={'Propuesta #' + id} subtitle="Revisión de compatibilidad y decisión auditada."><Link className="button secondary" to="/horarios/propuestas">Volver a propuestas</Link></PageHeader><div className="page-body"><ResourceState {...resource} />{resource.data && <DecisionForm key={resource.data.id + resource.data.status} proposal={resource.data} reload={resource.reload} />}</div></>;
}

function DecisionForm({ proposal: p, reload }: { proposal: Proposal; reload: () => void }) {
  const rooms = useResource<Classroom[]>('/classrooms/');
  const manage = useScheduler();
  const [room, setRoom] = useState(String(p.classroom));
  const [meetings, setMeetings] = useState(p.meetings);
  const [action, setAction] = useState(p.status === 'accepted' ? 'cancel' : 'accept');
  const [note, setNote] = useState('');
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit() {
    setBusy(true); setError('');
    try { await api('/assignments/' + p.id + '/decision/', 'POST', { action, note, ...(action === 'accept' ? { classroom: Number(room), meetings } : {}) }); reload(); }
    catch (e) { setError(errorText(e)); setConfirm(false); } finally { setBusy(false); }
  }
  return <><section className="panel detail-panel"><h2>{p.course_snapshot.code} · {p.course_snapshot.name}</h2><dl className="detail-grid"><div><dt>Estado</dt><dd>{statuses[p.status]}</dd></div><div><dt>Período</dt><dd>{p.date_from} a {p.date_to}</dd></div><div><dt>Aula</dt><dd>{p.classroom_name}</dd></div><div><dt>Matrícula / capacidad al {p.status === 'accepted' ? 'aceptar' : 'generar'}</dt><dd>{p.course_snapshot.enrollment} / {p.capacity_snapshot}</dd></div><div><dt>Docente</dt><dd>{p.course_snapshot.teacher_name}</dd></div><div><dt>Creada por</dt><dd>{p.creator_name} · {dateLabel(p.created_at)}</dd></div></dl><IntervalList value={p.meetings} /><details><summary>Motivos al generar la propuesta</summary><ul>{p.reasons.map(r => <li key={r}>{r}</li>)}</ul></details></section>
    {manage && ['pending', 'accepted'].includes(p.status) && <form className="panel entity-form" onSubmit={e => { e.preventDefault(); setConfirm(true); }}><h2>Revisar decisión</h2><fieldset disabled={busy || confirm}><div className="field"><label htmlFor="decision-action">Decisión</label><select id="decision-action" value={action} onChange={e => setAction(e.target.value)}>{(p.status === 'pending' ? ['accept', 'reject'] : ['cancel']).map(a => <option key={a} value={a}>{actions[a]}</option>)}</select></div>
      {action === 'accept' && <><ResourceState {...rooms} /><div className="field"><label htmlFor="decision-room">Aula propuesta o alternativa</label><select id="decision-room" required value={room} onChange={e => setRoom(e.target.value)}>{rooms.data?.map(r => <option key={r.id} value={r.id}>{r.name}{!r.active ? ' (inactiva)' : ''}</option>)}</select></div><IntervalEditor value={meetings} onChange={setMeetings} label="Franjas a asignar" /><p className="inline-empty">Puedes modificar aula o franjas. El servidor comprobará nuevamente todas las restricciones al confirmar.</p></>}
      <div className="field"><label htmlFor="decision-note">Motivo de la decisión</label><textarea id="decision-note" required minLength={5} maxLength={500} value={note} onChange={e => setNote(e.target.value)} /></div><button className="button primary">Revisar y confirmar</button>
    </fieldset>{confirm && <section className="schedule-confirm" aria-label="Confirmación de decisión"><h3>{actions[action]} propuesta #{p.id}</h3>{action === 'accept' && <><p>Aula: {rooms.data?.find(r => String(r.id) === room)?.name || p.classroom_name}</p><IntervalList value={meetings} /></>}<p>Período: {p.date_from} a {p.date_to}</p><p>Motivo: {note}</p><div className="table-actions"><button className="button primary" type="button" disabled={busy} onClick={() => void submit()}>Confirmar decisión</button><button className="button secondary" type="button" disabled={busy} onClick={() => setConfirm(false)}>Volver a editar</button></div></section>}<Message text={error} /></form>}
    <section className="panel detail-panel"><h2>Historial de decisiones</h2>{!p.decisions.length ? <p>Sin decisiones registradas.</p> : p.decisions.map((d, index) => <article className="decision-event" key={index}><strong>{actions[d.action]} · {d.actor}</strong><p>{dateLabel(d.created_at)} · {d.note}</p>{d.action === 'accept' && <><p>Aula #{d.before.classroom} → Aula #{d.after.classroom}</p><IntervalList value={d.after.meetings} /></>}</article>)}</section>
  </>;
}
