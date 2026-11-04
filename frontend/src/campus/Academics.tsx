import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, GraduationCap, Plus, Save } from 'lucide-react';
import { api } from '../api';
import { Message } from '../components';
import type { Course, Interval, Subject, Teacher } from './types';
import { AcademicTabs, ActiveField, equipmentFrom, errorText, IntervalEditor, IntervalList, PageHeader, ReadOnlyNotice, ResourceState, Status, useCanManage, useResource } from './shared';

type CatalogKind = 'teachers' | 'subjects';
const catalogConfig = {
  teachers: { route: 'docentes', title: 'Docentes', singular: 'docente', newLabel: 'Nuevo docente' },
  subjects: { route: 'asignaturas', title: 'Asignaturas', singular: 'asignatura', newLabel: 'Nueva asignatura' },
};
function SimulatedNotice() { return <p className="academic-note">Datos académicos simulados para planificación. No están conectados a una matrícula institucional.</p>; }

export function CatalogList({ kind }: { kind: CatalogKind }) {
  const manage = useCanManage();
  const config = catalogConfig[kind];
  const [search, setSearch] = useState('');
  const result = useResource<(Teacher & Subject)[]>(`/${kind}/?search=${encodeURIComponent(search)}`);
  return <><PageHeader title="Datos académicos" subtitle="Organiza cursos, docentes, asignaturas y matrícula.">
    {manage && <Link className="button primary" to={`/academico/${config.route}/nuevo`}><Plus size={16} />{config.newLabel}</Link>}
  </PageHeader><div className="page-body"><AcademicTabs /><SimulatedNotice />{!manage && <ReadOnlyNotice />}
    <div className="filters-row"><div className="field"><label htmlFor="catalog-search">Buscar {config.title.toLowerCase()}</label><input id="catalog-search" type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Nombre, código o correo" /></div></div>
    <ResourceState {...result} />{result.data && <section className="panel table-wrap"><table><thead><tr><th>Nombre</th><th>{kind === 'teachers' ? 'Correo' : 'Código'}</th><th>Estado</th><th>Acciones</th></tr></thead>
      <tbody>{result.data.map(record => <tr key={record.id}><td><strong>{record.name}</strong></td><td>{kind === 'teachers' ? record.email : record.code}</td><td><Status active={record.active} /></td><td>{manage ? <Link className="button secondary small" to={`/academico/${config.route}/${record.id}/editar`}>Editar</Link> : <span className="small-muted">Solo consulta</span>}</td></tr>)}</tbody></table>
      {result.data.length === 0 && <div className="empty-state compact"><GraduationCap size={32} /><h3>No hay {config.title.toLowerCase()} para mostrar</h3><p>{search ? 'Prueba otra búsqueda.' : 'Los registros aparecerán aquí.'}</p></div>}
    </section>}
  </div></>;
}

export function CatalogEditor({ kind }: { kind: CatalogKind }) {
  const { id } = useParams();
  const manage = useCanManage();
  const config = catalogConfig[kind];
  const result = useResource<(Teacher & Subject) | (Teacher & Subject)[]>(id ? `/${kind}/${id}/` : `/${kind}/`);
  if (!manage) return <div className="page-body"><ReadOnlyNotice /><Link to={`/academico/${config.route}`}>Volver al listado</Link></div>;
  return <><PageHeader title={id ? `Editar ${config.singular}` : config.newLabel} subtitle="Información académica de referencia." /><div className="page-body">
    <ResourceState {...result} />{result.data && <CatalogForm key={`${kind}-${id || 'new'}`} kind={kind} record={id ? result.data as Teacher & Subject : undefined} />}
  </div></>;
}

function CatalogForm({ kind, record }: { kind: CatalogKind; record?: Teacher & Subject }) {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const target = `/academico/${catalogConfig[kind].route}`;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true);
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      await api(record ? `/${kind}/${record.id}/` : `/${kind}/`, record ? 'PATCH' : 'POST', { ...values, active: values.active === 'true' });
      navigate(target);
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <form className="panel entity-form" onSubmit={submit}><fieldset disabled={busy}>
    <div className="field"><label htmlFor="name">Nombre</label><input id="name" name="name" required maxLength={150} defaultValue={record?.name} /></div>
    {kind === 'teachers' ? <div className="field"><label htmlFor="email">Correo</label><input id="email" name="email" type="email" required maxLength={254} defaultValue={record?.email} /></div> :
      <div className="field"><label htmlFor="code">Código</label><input id="code" name="code" required maxLength={30} defaultValue={record?.code} placeholder="Ej. CS-101" /></div>}
    <ActiveField value={record?.active} />
    <p className="small-muted form-note">Para desactivar este registro, primero desactiva o reasigna sus cursos activos.</p>
    <Message text={error} /><div className="form-actions"><Link className="button secondary" to={target}>Cancelar</Link><button className="button primary" disabled={busy}><Save size={16} />{busy ? 'Guardando…' : 'Guardar'}</button></div>
  </fieldset></form>;
}

export function CourseList() {
  const manage = useCanManage();
  const [search, setSearch] = useState('');
  const [active, setActive] = useState('');
  const result = useResource<Course[]>(`/courses/?${new URLSearchParams({ search, active })}`);
  return <><PageHeader title="Datos académicos" subtitle="Organiza cursos, docentes, asignaturas y matrícula.">
    {manage && <Link className="button primary" to="/academico/cursos/nuevo"><Plus size={16} />Nuevo curso</Link>}
  </PageHeader><div className="page-body"><AcademicTabs /><SimulatedNotice />{!manage && <ReadOnlyNotice />}
    <div className="filters-row"><div className="field"><label htmlFor="course-search">Buscar cursos</label><input id="course-search" type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Curso, asignatura o docente" /></div><div className="field"><label htmlFor="course-active">Estado</label><select id="course-active" value={active} onChange={e => setActive(e.target.value)}><option value="">Todos</option><option value="true">Activo</option><option value="false">Inactivo</option></select></div></div>
    <ResourceState {...result} />{result.data && <section className="panel table-wrap"><table><thead><tr><th>Curso</th><th>Asignatura</th><th>Docente</th><th>Matrícula</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>
      {result.data.map(course => <tr key={course.id}><td><strong>{course.name}</strong><small>{course.code}</small></td><td>{course.subject_name}</td><td>{course.teacher_name}</td><td>{course.enrollment}</td><td><Status active={course.active} /></td><td><div className="table-actions">{manage && <Link className="button secondary small" to={`/academico/cursos/${course.id}/editar`}>Editar</Link>}<Link className="button primary small" to={`/academico/cursos/${course.id}`}>Ver</Link></div></td></tr>)}
    </tbody></table>{result.data.length === 0 && <div className="empty-state compact"><GraduationCap size={32} /><h3>No hay cursos para mostrar</h3><p>{search || active ? 'Prueba otros filtros.' : 'Registra docentes y asignaturas para crear el primer curso.'}</p>{manage && !search && !active && <Link className="button secondary" to="/academico/docentes">Gestionar docentes</Link>}</div>}</section>}
  </div></>;
}

export function CourseEditor() {
  const { id } = useParams();
  const manage = useCanManage();
  const course = useResource<Course | Course[]>(id ? `/courses/${id}/` : '/courses/');
  const teachers = useResource<Teacher[]>('/teachers/');
  const subjects = useResource<Subject[]>('/subjects/');
  if (!manage) return <div className="page-body"><ReadOnlyNotice /><Link to="/academico/cursos">Volver a cursos</Link></div>;
  return <><PageHeader title={id ? 'Editar curso' : 'Registrar un nuevo curso'} subtitle="Matrícula, docente y franjas semanales." /><div className="page-body">
    <ResourceState {...course} /><ResourceState {...teachers} /><ResourceState {...subjects} />
    {course.data && teachers.data && subjects.data && <CourseForm key={id || 'new'} course={id ? course.data as Course : undefined} teachers={teachers.data} subjects={subjects.data} />}
  </div></>;
}

function CourseForm({ course, teachers, subjects }: { course?: Course; teachers: Teacher[]; subjects: Subject[] }) {
  const navigate = useNavigate();
  const [meetings, setMeetings] = useState<Interval[]>(course?.meetings || []);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  if (!teachers.length || !subjects.length) return <section className="panel detail-panel"><h2>Completa los datos de referencia</h2><p className="inline-empty">Necesitas al menos un docente y una asignatura antes de registrar cursos.</p><div className="table-actions"><Link className="button secondary" to="/academico/docentes">Gestionar docentes</Link><Link className="button secondary" to="/academico/asignaturas">Gestionar asignaturas</Link><Link className="button secondary" to="/academico/cursos">Volver</Link></div></section>;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true);
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const result = await api<Course>(course ? `/courses/${course.id}/` : '/courses/', course ? 'PATCH' : 'POST', {
        ...values, teacher: Number(values.teacher), subject: Number(values.subject),
        enrollment: Number(values.enrollment), active: values.active === 'true',
        required_equipment: equipmentFrom(String(values.required_equipment)), meetings,
      });
      navigate(`/academico/cursos/${result.id}`);
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <form className="panel entity-form" onSubmit={submit}><fieldset disabled={busy}>
    <div className="form-grid"><div className="field"><label htmlFor="code">Código</label><input id="code" name="code" required maxLength={30} defaultValue={course?.code} placeholder="Ej. CS-5A" /></div>
      <div className="field"><label htmlFor="name">Nombre del curso</label><input id="name" name="name" required maxLength={150} defaultValue={course?.name} placeholder="Ej. Quinto semestre A" /></div></div>
    <div className="form-grid"><div className="field"><label htmlFor="subject">Asignatura</label><select id="subject" name="subject" defaultValue={course?.subject || ''} required><option value="">Selecciona una asignatura</option>{subjects.map(s => <option key={s.id} value={s.id}>{s.code} · {s.name}{!s.active ? ' (inactiva)' : ''}</option>)}</select></div>
      <div className="field"><label htmlFor="teacher">Docente</label><select id="teacher" name="teacher" defaultValue={course?.teacher || ''} required><option value="">Selecciona un docente</option>{teachers.map(t => <option key={t.id} value={t.id}>{t.name}{!t.active ? ' (inactivo)' : ''}</option>)}</select></div></div>
    <div className="form-grid"><div className="field"><label htmlFor="enrollment">Estudiantes matriculados</label><input id="enrollment" name="enrollment" type="number" required min={0} max={10000} step={1} defaultValue={course?.enrollment ?? 0} /></div><ActiveField value={course?.active} /></div>
    <div className="field"><label htmlFor="required-equipment">Equipamiento requerido (separado por comas)</label><input id="required-equipment" name="required_equipment" defaultValue={course?.required_equipment.join(', ')} placeholder="Computadores, proyector" /></div>
    <IntervalEditor value={meetings} onChange={setMeetings} label="Franjas del curso" />
    <p className="small-muted form-note">Un curso puede guardarse sin franjas para completar sus datos después. La asignación de aulas necesitará un horario definido.</p>
    <Message text={error} /><div className="form-actions"><Link className="button secondary" to={course ? `/academico/cursos/${course.id}` : '/academico/cursos'}>Cancelar</Link><button className="button primary" disabled={busy}><Save size={16} />{busy ? 'Guardando…' : 'Guardar'}</button></div>
  </fieldset></form>;
}

export function CourseDetail() {
  const { id } = useParams();
  const manage = useCanManage();
  const result = useResource<Course>(`/courses/${id}/`);
  return <><PageHeader title={result.data?.name || 'Detalle del curso'} subtitle="Información académica simulada."><Link className="button secondary" to="/academico/cursos"><ArrowLeft size={16} />Volver a cursos</Link></PageHeader>
    <div className="page-body detail-stack"><ResourceState {...result} />{result.data && <><section className="panel detail-panel"><div className="panel-title-row"><h2>{result.data.code}</h2><Status active={result.data.active} /></div><dl className="detail-grid">
      <div><dt>Asignatura</dt><dd>{result.data.subject_name}</dd></div><div><dt>Docente</dt><dd>{result.data.teacher_name}</dd></div><div><dt>Estudiantes matriculados</dt><dd>{result.data.enrollment}</dd></div><div><dt>Equipamiento requerido</dt><dd>{result.data.required_equipment.join(', ') || 'Sin requisitos registrados'}</dd></div>
    </dl>{manage && <Link className="button secondary" to={`/academico/cursos/${id}/editar`}>Editar curso</Link>}</section><section className="panel detail-panel"><h2>Franjas semanales</h2><IntervalList value={result.data.meetings} /></section></>}</div>
  </>;
}
