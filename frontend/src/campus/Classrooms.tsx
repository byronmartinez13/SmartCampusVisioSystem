import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Building2, Plus, Save, ShieldCheck } from 'lucide-react';
import { api } from '../api';
import { Message } from '../components';
import type { Classroom, Interval, Validation, Activity } from './types';
import { ActiveField, dateLabel, equipmentFrom, errorText, IntervalEditor, IntervalList, PageHeader, ReadOnlyNotice, ResourceState, Status, useCanManage, useResource } from './shared';

export function Classrooms() {
  const manage = useCanManage();
  const [search, setSearch] = useState('');
  const [kind, setKind] = useState('');
  const [active, setActive] = useState('');
  const result = useResource<Classroom[]>(`/classrooms/?${new URLSearchParams({ search, kind, active })}`);
  return <><PageHeader title="Aulas y Laboratorios" subtitle="Gestiona los espacios académicos y su capacidad.">
    {manage && <Link className="button primary" to="/aulas/nueva"><Plus size={16} />Nueva Aula/Laboratorio</Link>}
  </PageHeader><div className="page-body">
    {!manage && <ReadOnlyNotice />}
    <div className="filters-row"><div className="field"><label htmlFor="search">Buscar</label><input id="search" type="search" placeholder="Nombre o ubicación" value={search} onChange={e => setSearch(e.target.value)} /></div>
      <div className="field"><label htmlFor="kind-filter">Tipo</label><select id="kind-filter" value={kind} onChange={e => setKind(e.target.value)}><option value="">Todos los espacios</option><option value="classroom">Aulas</option><option value="lab">Laboratorios</option></select></div>
      <div className="field"><label htmlFor="status-filter">Estado</label><select id="status-filter" value={active} onChange={e => setActive(e.target.value)}><option value="">Todos</option><option value="true">Activo</option><option value="false">Inactivo</option></select></div>
    </div><ResourceState {...result} />
    {result.data && <section className="panel table-wrap"><table><thead><tr><th>Nombre</th><th>Tipo</th><th>Capacidad declarada</th><th>Cámara asociada</th><th>Estado</th><th>Acciones</th></tr></thead>
      <tbody>{result.data.map(room => <tr key={room.id}><td><strong>{room.name}</strong><small>{room.location || 'Sin ubicación'}</small></td><td>{room.kind_label}</td><td>{room.capacity === null ? 'Sin definir' : `${room.capacity} puestos`}</td><td>{room.camera_label || room.camera_display}</td><td><Status active={room.active} /></td><td><div className="table-actions">{manage && <Link className="button secondary small" to={`/aulas/${room.id}/editar`}>Editar</Link>}<Link className="button primary small" to={`/aulas/${room.id}`}>Ver</Link></div></td></tr>)}</tbody></table>
      {result.data.length === 0 && <div className="empty-state compact"><Building2 size={32} /><h3>No hay espacios para mostrar</h3><p>{search || kind || active ? 'Prueba otros filtros.' : 'Los espacios registrados aparecerán aquí.'}</p></div>}
    </section>}
  </div></>;
}

export function ClassroomEditor() {
  const { id } = useParams();
  const manage = useCanManage();
  const result = useResource<Classroom | Classroom[]>(id ? `/classrooms/${id}/` : '/classrooms/');
  if (!manage) return <div className="page-body"><ReadOnlyNotice /><Link to="/aulas">Volver a aulas</Link></div>;
  return <><PageHeader title={id ? 'Editar Aula/Laboratorio' : 'Registrar una nueva Aula/Laboratorio'} subtitle="Información, equipamiento y disponibilidad del espacio." /><div className="page-body">
    <ResourceState {...result} />{result.data && <RoomForm key={id || 'new'} room={id ? result.data as Classroom : undefined} />}
  </div></>;
}

function RoomForm({ room }: { room?: Classroom }) {
  const navigate = useNavigate();
  const [availability, setAvailability] = useState<Interval[]>(room?.availability || []);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true);
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const result = await api<Classroom>(room ? `/classrooms/${room.id}/` : '/classrooms/', room ? 'PATCH' : 'POST', {
        ...values, capacity: values.capacity === '' ? null : Number(values.capacity),
        active: values.active === 'true', equipment: equipmentFrom(String(values.equipment)), availability,
      });
      navigate(`/aulas/${result.id}`, { state: { saved: true } });
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <form className="panel entity-form" onSubmit={save}><fieldset disabled={busy}>
    <div className="field"><label htmlFor="name">Nombre</label><input id="name" name="name" defaultValue={room?.name} required maxLength={150} placeholder="Ej. Semillero de programación" /></div>
    <div className="form-grid"><div className="field"><label htmlFor="kind">Tipo</label><select id="kind" name="kind" defaultValue={room?.kind || 'classroom'}><option value="classroom">Aula</option><option value="lab">Laboratorio</option></select></div>
      <div className="field"><label htmlFor="capacity">Capacidad declarada</label><input id="capacity" name="capacity" type="number" min={0} max={10000} step={1} defaultValue={room?.capacity ?? ''} placeholder="Sin definir" /></div></div>
    <div className="field"><label htmlFor="location">Ubicación</label><input id="location" name="location" defaultValue={room?.location} maxLength={200} placeholder="Bloque, piso o referencia" /></div>
    <div className="form-grid"><div className="field"><label htmlFor="camera">Cámara</label><select id="camera" name="camera" defaultValue={room?.camera || 'none'}><option value="none">Sin cámara</option><option value="integrated">Cámara integrada</option><option value="usb">Cámara USB</option><option value="rtsp">Cámara IP / RTSP</option></select></div>
      <div className="field"><label htmlFor="camera_label">Identificador de cámara</label><input id="camera_label" name="camera_label" defaultValue={room?.camera_label} maxLength={100} placeholder="Ej. Cámara 01" /></div></div>
    <p className="small-muted form-note">La cámara se registra como referencia. La conexión y su prueba estarán disponibles con el módulo de análisis.</p>
    <div className="field"><label htmlFor="equipment">Equipamiento (separado por comas)</label><input id="equipment" name="equipment" defaultValue={room?.equipment.join(', ')} placeholder="Computadores, proyector, pizarra" /></div>
    <ActiveField value={room?.active} />
    <IntervalEditor value={availability} onChange={setAvailability} label="Disponibilidad semanal" />
    {room?.validated_capacity !== null && room?.validated_capacity !== undefined && <p className="read-only-note">Cambiar la capacidad declarada, el tipo o el equipamiento requerirá validar nuevamente la capacidad.</p>}
    <Message text={error} /><div className="form-actions"><Link className="button secondary" to={room ? `/aulas/${room.id}` : '/aulas'}>Cancelar</Link><button className="button primary" disabled={busy}><Save size={16} />{busy ? 'Guardando…' : 'Guardar'}</button></div>
  </fieldset></form>;
}

export function ClassroomDetail() {
  const { id } = useParams();
  const manage = useCanManage();
  const room = useResource<Classroom>(`/classrooms/${id}/`);
  const history = useResource<Validation[]>(`/classrooms/${id}/validations/`);
  const activity = useResource<Activity[]>(`/classrooms/${id}/activity/`);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [busy, setBusy] = useState(false);
  async function validate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    setBusy(true); setError(''); setSuccess('');
    try {
      await api(`/classrooms/${id}/validate-capacity/`, 'POST', { value: Number(values.value), note: values.note });
      room.reload(); history.reload(); setSuccess('Capacidad validada y registrada en el historial.'); form.reset();
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <><PageHeader title={room.data?.name || 'Detalle del espacio'} subtitle="Información del aula o laboratorio.">
    <Link to="/aulas" className="button secondary"><ArrowLeft size={16} />Volver a aulas</Link>
  </PageHeader><div className="page-body detail-stack"><ResourceState {...room} />
    <Message text={success} success /><Message text={error} />
    {room.data && <>
      <section className="panel detail-panel"><div className="panel-title-row"><h2>Información general</h2><Status active={room.data.active} /></div>
        <dl className="detail-grid"><div><dt>Tipo</dt><dd>{room.data.kind_label}</dd></div><div><dt>Ubicación</dt><dd>{room.data.location || 'Sin ubicación'}</dd></div><div><dt>Capacidad declarada</dt><dd>{room.data.capacity ?? 'Sin definir'}</dd></div><div><dt>Capacidad validada</dt><dd>{room.data.validated_capacity ?? 'Pendiente de validación'}</dd></div><div><dt>Cámara</dt><dd>{room.data.camera_label || room.data.camera_display}</dd><small>Conexión sin comprobar</small></div><div><dt>Equipamiento</dt><dd>{room.data.equipment.join(', ') || 'Sin equipamiento registrado'}</dd></div></dl>
        {room.data.capacity_validated_at && <p className="small-muted">Validada por {room.data.validated_by_name} · {dateLabel(room.data.capacity_validated_at)}</p>}
        {manage && <Link className="button secondary" to={`/aulas/${id}/editar`}>Editar Aula</Link>}
        <div className="analysis-actions"><Link className="button secondary" to={`/historial?classroom=${id}`}>Historial de análisis del aula</Link><Link className="button secondary" to={`/reportes?classroom=${id}`}>Reporte del aula</Link></div>
      </section>
      <section className="panel detail-panel"><h2>Disponibilidad semanal</h2><IntervalList value={room.data.availability} /></section>
      {manage && <section className="panel detail-panel"><h2><ShieldCheck size={20} />Validar capacidad</h2><p className="small-muted">Registra el número de puestos comprobado por una persona. Esta validación será la referencia para las recomendaciones.</p>
        <form onSubmit={validate}><fieldset disabled={busy}><div className="form-grid"><div className="field"><label htmlFor="validated-value">Puestos comprobados</label><input id="validated-value" name="value" type="number" min={0} max={10000} step={1} required /></div><div className="field"><label htmlFor="validation-note">Observación</label><input id="validation-note" name="note" minLength={5} maxLength={500} required placeholder="Cómo y cuándo se verificó el espacio" /></div></div>
          <button className="button primary" disabled={busy}>{busy ? 'Guardando…' : 'Confirmar validación'}</button></fieldset></form></section>}
      <section className="panel detail-panel"><h2>Historial de validaciones</h2><ResourceState {...history} />{history.data?.length === 0 && <p className="inline-empty">No hay validaciones registradas.</p>}
        {history.data && history.data.length > 0 && <div className="table-wrap"><table><thead><tr><th>Fecha</th><th>Puestos</th><th>Responsable</th><th>Observación</th></tr></thead><tbody>{history.data.map(row => <tr key={row.id}><td>{dateLabel(row.created_at)}</td><td>{row.value}</td><td>{row.actor_name}</td><td>{row.note}</td></tr>)}</tbody></table></div>}
      </section>
      <section className="panel detail-panel"><h2>Actividad reciente</h2><ResourceState {...activity} />{activity.data?.length === 0 && <p className="inline-empty">Este espacio todavía no tiene análisis registrados.</p>}
        {activity.data && activity.data.length > 0 && <div className="table-wrap"><table><thead><tr><th>Fecha</th><th>Personas</th><th>Capacidad del análisis</th><th>Ocupación</th></tr></thead><tbody>{activity.data.map(row => <tr key={row.id}><td>{dateLabel(row.created_at)}</td><td>{row.people}</td><td>{row.capacity ?? 'Sin definir'}</td><td>{row.occupancy === null ? 'No calculable' : `${row.occupancy}%`}</td></tr>)}</tbody></table></div>}
      </section>
    </>}
  </div></>;
}
