import { useEffect, useState, type ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { Plus, Trash2 } from 'lucide-react';
import { api } from '../api';
import { useAuth } from '../auth';
import { Message } from '../components';
import type { Interval } from './types';

export const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
export const equipmentFrom = (text: string) => text.split(',').map(s => s.trim()).filter(Boolean);
export const dateLabel = (text: string) => {
  const date = new Date(text);
  if (localStorage.getItem('date-format') === 'ymd') {
    const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Guayaquil', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(date);
    const value = (key: string) => parts.find(p => p.type === key)?.value;
    return `${value('year')}-${value('month')}-${value('day')} ${value('hour')}:${value('minute')}`;
  }
  return date.toLocaleString('es-EC', { timeZone: 'America/Guayaquil' });
};
export const errorText = (e: unknown) => e instanceof Error ? e.message : 'No se pudo completar la operación.';
export function useCanManage() { const { user } = useAuth(); return user?.role === 'admin'; }

export function useResource<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let current = true;
    setLoading(true); setError(''); setData(null);
    api<T>(path).then(value => { if (current) setData(value); })
      .catch(e => { if (current) setError(errorText(e)); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [path, revision]);
  return { data, error, loading, reload: () => setRevision(value => value + 1) };
}

export function PageHeader({ title, subtitle, children }: { title: string; subtitle: string; children?: ReactNode }) {
  return <header className="page-header"><div><h1>{title}</h1><p>{subtitle}</p></div>{children}</header>;
}
export function ResourceState({ loading, error, reload }: { loading: boolean; error: string; reload: () => void }) {
  return <>{loading && <p className="loading-state" role="status">Cargando información…</p>}
    <Message text={error} />{error && <button className="button secondary" onClick={reload}>Reintentar</button>}</>;
}
export function ReadOnlyNotice() {
  return <p className="read-only-note">Tu cuenta tiene acceso de consulta. Un administrador puede crear o modificar estos registros.</p>;
}
export function Status({ active }: { active: boolean }) {
  return <span className={`record-status ${active ? 'is-active' : 'is-inactive'}`}>{active ? 'Activo' : 'Inactivo'}</span>;
}
export function ActiveField({ value = true }: { value?: boolean }) {
  return <div className="field"><label htmlFor="active">Estado</label><select id="active" name="active" defaultValue={String(value)}><option value="true">Activo</option><option value="false">Inactivo</option></select></div>;
}
export function AcademicTabs() {
  return <nav className="academic-tabs" aria-label="Datos académicos">
    <NavLink to="/academico/cursos">Cursos</NavLink><NavLink to="/academico/docentes">Docentes</NavLink><NavLink to="/academico/asignaturas">Asignaturas</NavLink>
  </nav>;
}
export function IntervalEditor({ value, onChange, label }: { value: Interval[]; onChange: (value: Interval[]) => void; label: string }) {
  function update(index: number, key: keyof Interval, input: string) {
    onChange(value.map((row, i) => i === index ? { ...row, [key]: key === 'weekday' ? Number(input) : input } : row));
  }
  return <div className="interval-editor"><h3>{label}</h3>
    <p className="small-muted">Franjas semanales. La hora final debe ser posterior a la inicial; no se permiten superposiciones.</p>
    {value.length === 0 && <p className="inline-empty">Sin franjas configuradas.</p>}
    {value.map((row, i) => <div className="interval-row" key={i}>
      <div className="field"><label htmlFor={`weekday-${i}`}>Día {i + 1}</label><select id={`weekday-${i}`} value={row.weekday} onChange={e => update(i, 'weekday', e.target.value)}>{days.map((day, index) => <option value={index} key={day}>{day}</option>)}</select></div>
      <div className="field"><label htmlFor={`start-${i}`}>Inicio {i + 1}</label><input id={`start-${i}`} type="time" required value={row.start} onChange={e => update(i, 'start', e.target.value)} /></div>
      <div className="field"><label htmlFor={`end-${i}`}>Fin {i + 1}</label><input id={`end-${i}`} type="time" required value={row.end} onChange={e => update(i, 'end', e.target.value)} /></div>
      <button className="button secondary remove-slot" type="button" aria-label={`Quitar franja ${i + 1}`} onClick={() => onChange(value.filter((_, index) => index !== i))}><Trash2 size={16} /></button>
    </div>)}
    <button className="button secondary" type="button" onClick={() => onChange([...value, { weekday: 0, start: '08:00', end: '10:00' }])}><Plus size={16} />Añadir franja</button>
  </div>;
}
export function IntervalList({ value }: { value: Interval[] }) {
  return value.length ? <ul className="interval-list">{value.map((row, i) => <li key={i}><strong>{days[row.weekday]}</strong><span>{row.start}–{row.end}</span></li>)}</ul> : <p className="small-muted">Sin franjas configuradas.</p>;
}
