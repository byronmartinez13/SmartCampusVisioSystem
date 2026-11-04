import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { api, type User } from './api';
import { useAuth } from './auth';
import { Message } from './components';
import { dateLabel, errorText, PageHeader, ReadOnlyNotice, ResourceState, useCanManage, useResource } from './campus/shared';

export type Preferences = { confidence: number; auto_save: boolean; auto_pdf: boolean; record_live: boolean;
  alerts_enabled: boolean; alert_threshold: number; date_format: string; version: number };
type Rule = { id: number; kind: string; label: string; value: string; active: boolean; version: number };
const kinds: Record<string, string> = { min_spare: 'Puestos de reserva (1 a 1000)', max_enrollment: 'Matrícula máxima (1 a 1000)', extra_equipment: 'Equipo obligatorio (nombre del catálogo)', preferred_kind: 'Preferencia de aula o laboratorio' };
function RuleValue({ kind, id, value = '' }: { kind: string; id: string; value?: string }) {
  return kind === 'preferred_kind'
    ? <select id={id} name="value" defaultValue={value || 'classroom'}><option value="classroom">Aula</option><option value="lab">Laboratorio</option></select>
    : <input id={id} name="value" defaultValue={value} type={kind === 'extra_equipment' ? 'text' : 'number'} min={1} max={1000} step={1} maxLength={100} required />;
}

export function GeneralSettings() {
  const resource = useResource<Preferences>('/settings/');
  const manage = useCanManage();
  const [error, setError] = useState(''); const [message, setMessage] = useState(''); const [busy, setBusy] = useState(false);
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setBusy(true); setError(''); setMessage('');
    const form = new FormData(e.currentTarget);
    const data = { confidence: Number(form.get('confidence')), alert_threshold: Number(form.get('alert_threshold')),
      date_format: String(form.get('date_format')), version: resource.data!.version,
      ...Object.fromEntries(['auto_save', 'auto_pdf', 'record_live', 'alerts_enabled'].map(k => [k, form.has(k)])) };
    try { const saved = await api<Preferences>('/settings/', 'PATCH', data); localStorage.setItem('date-format', saved.date_format); setMessage('Configuración guardada. Se aplicará a los nuevos análisis.'); resource.reload(); }
    catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <section className="panel settings-panel"><h2>Configuración general</h2><ResourceState {...resource} /><Message text={error} /><Message text={message} success />
    {!manage && <ReadOnlyNotice />}{resource.data && <form key={resource.data.version} onSubmit={save}><fieldset disabled={!manage || busy}>
      <div className="field"><label htmlFor="default-confidence">Confianza predeterminada del detector</label><input id="default-confidence" name="confidence" type="number" min="0.1" max="0.95" step="0.05" defaultValue={resource.data.confidence} required /></div>
      <div className="field"><label htmlFor="alert-threshold">Umbral de alerta (% de capacidad validada)</label><input id="alert-threshold" name="alert_threshold" type="number" min="1" max="200" defaultValue={resource.data.alert_threshold} required /></div>
      <div className="field"><label htmlFor="date-format">Formato de fecha</label><select id="date-format" name="date_format" defaultValue={resource.data.date_format}><option value="dmy">Día / mes / año</option><option value="ymd">Año - mes - día</option></select></div>
      {([['auto_save', 'Guardar automáticamente el resumen al finalizar'], ['auto_pdf', 'Descargar PDF al abrir un resultado completado'], ['record_live', 'Ofrecer grabación local de cámara'], ['alerts_enabled', 'Crear alertas al superar el umbral']] as const).map(([key, label]) => <label className="setting-check" key={key}><input type="checkbox" name={key} defaultChecked={resource.data![key]} /> {label}</label>)}
      <p className="small-muted">Las opciones se conservan en cada análisis. Cambiar el umbral no modifica alertas anteriores. La grabación se descarga en el navegador y no se conserva en el servidor.</p>
      {manage && <button className="button primary" disabled={busy}>Guardar configuración general</button>}
    </fieldset></form>}
    <p><Link to="/administracion/reglas">Reglas de asignación</Link>{manage && <> · <Link to="/administracion/usuarios">Usuarios y roles</Link> · <Link to="/administracion/auditoria">Auditoría administrativa</Link></>}</p>
  </section>;
}

export function Rules() {
  const resource = useResource<Rule[]>('/assignment-rules/'); const manage = useCanManage();
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const [newKind, setNewKind] = useState('min_spare');
  async function save(e: FormEvent<HTMLFormElement>, rule?: Rule) {
    e.preventDefault(); setError(''); setBusy(true); const form = e.currentTarget; const data = new FormData(form);
    try { await api(`/assignment-rules/${rule ? `${rule.id}/` : ''}`, rule ? 'PATCH' : 'POST', {
      kind: rule?.kind || data.get('kind'), value: data.get('value'), active: data.has('active'), ...(rule ? { version: rule.version } : {}) });
      if (!rule) form.reset(); resource.reload();
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <><PageHeader title="Reglas de asignación" subtitle="Restricciones adicionales y preferencias persistentes del motor de alternativas." /><div className="page-body"><Message text={error} /><ResourceState {...resource} />
    <section className="panel settings-panel"><h2>Restricciones fundamentales</h2><p>Siempre se exige capacidad validada suficiente, disponibilidad, equipamiento del curso y ausencia de cruces. Las reglas adicionales nunca desactivan esas restricciones.</p><p>Los puestos de reserva y el equipo adicional son obligatorios. La preferencia de espacio solo ordena alternativas compatibles y puede ajustarse en cada propuesta.</p></section>
    {!manage && <ReadOnlyNotice />}{manage && <section className="panel settings-panel"><h2>Nueva regla</h2><form onSubmit={e => void save(e)}><fieldset disabled={busy}><div className="field"><label htmlFor="rule-kind">Tipo de regla</label><select id="rule-kind" name="kind" value={newKind} onChange={e => setNewKind(e.target.value)}>{Object.entries(kinds).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div><div className="field"><label htmlFor="rule-value">Valor</label><RuleValue kind={newKind} id="rule-value" key={newKind} /></div><label className="setting-check"><input type="checkbox" name="active" defaultChecked /> Activa</label><button className="button primary">Registrar regla</button></fieldset></form></section>}
    {resource.data?.map(rule => <section className="panel settings-panel" key={`${rule.id}-${rule.version}`}><h2>{rule.label}</h2><form onSubmit={e => void save(e, rule)}><fieldset disabled={busy || !manage}><div className="field"><label htmlFor={`rule-${rule.id}`}>{kinds[rule.kind]}</label><RuleValue kind={rule.kind} id={`rule-${rule.id}`} value={rule.value} /></div><label className="setting-check"><input name="active" type="checkbox" defaultChecked={rule.active} /> Activa</label>{manage && <button className="button secondary">Guardar regla</button>}</fieldset></form></section>)}
    {resource.data?.length === 0 && <p>No hay reglas adicionales. Se aplican las restricciones fundamentales.</p>}
  </div></>;
}

export function Users() {
  const { user } = useAuth(); const manage = useCanManage();
  return <><PageHeader title="Usuarios y roles" subtitle="Cambios de acceso con motivo y auditoría. No modifica contraseñas ni permisos de Django admin." /><div className="page-body">{manage ? <UserList currentId={user!.id} /> : <ReadOnlyNotice />}</div></>;
}

function UserList({ currentId }: { currentId: number }) {
  const resource = useResource<User[]>('/auth/users/'); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  async function save(e: FormEvent<HTMLFormElement>, id: number) {
    e.preventDefault(); const data = new FormData(e.currentTarget); setError(''); setBusy(true);
    try { await api(`/auth/users/${id}/access/`, 'PATCH', { role: data.get('role'), is_active: data.has('is_active'), note: data.get('note') }); resource.reload(); }
    catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <><Message text={error} /><ResourceState {...resource} />{resource.data?.map(u => <section className="panel settings-panel" key={`${u.id}-${u.role}-${u.is_active}`}><h2>{u.name}</h2><p>{u.email}{u.id === currentId ? ' · Tu cuenta' : ''}</p><form onSubmit={e => void save(e, u.id)}><fieldset disabled={busy || u.id === currentId}>
    <div className="field"><label htmlFor={`role-${u.id}`}>Rol de {u.name}</label><select id={`role-${u.id}`} name="role" defaultValue={u.role}><option value="viewer">Consulta</option><option value="coordinator">Coordinador</option><option value="admin">Administrador</option></select></div>
    <label className="setting-check"><input type="checkbox" name="is_active" defaultChecked={u.is_active} /> Cuenta activa</label>
    <div className="field"><label htmlFor={`note-${u.id}`}>Motivo del cambio de {u.name}</label><input id={`note-${u.id}`} name="note" minLength={5} maxLength={500} required /></div>
    <label className="setting-check"><input type="checkbox" required /> Confirmo el cambio de acceso para esta cuenta</label><button className="button secondary">Guardar acceso</button>
  </fieldset></form></section>)}</>;
}

export function AdministrativeAudit() {
  const manage = useCanManage();
  return <><PageHeader title="Auditoría administrativa" subtitle="Últimos 100 cambios de configuración, reglas y acceso." /><div className="page-body">{manage ? <AuditList /> : <ReadOnlyNotice />}</div></>;
}
function AuditList() {
  const actions: Record<string, string> = { 'user.access': 'Acceso de usuario actualizado', 'settings.updated': 'Configuración actualizada', 'rule.created': 'Regla registrada', 'rule.updated': 'Regla actualizada' };
  const resource = useResource<{ id: number; actor: string; action: string; target: string; created_at: string; before: unknown; after: unknown }[]>('/administrative-events/');
  return <><ResourceState {...resource} />{resource.data?.map(e => <article className="panel settings-panel" key={e.id}><h2>{actions[e.action] || 'Cambio administrativo'}</h2><p>{dateLabel(e.created_at)} · {e.actor} · {e.target === 'system' ? 'Configuración general' : `Registro ${e.target}`}</p><details><summary>Ver cambio</summary><h3>Antes</h3><AuditValues value={e.before} /><h3>Después</h3><AuditValues value={e.after} /></details></article>)}{resource.data?.length === 0 && <p>No hay cambios registrados.</p>}</>;
}

function AuditValues({ value }: { value: unknown }) {
  const labels: Record<string, string> = { role: 'Rol', is_active: 'Cuenta activa', note: 'Motivo', confidence: 'Confianza', auto_save: 'Guardado automático', auto_pdf: 'PDF automático', record_live: 'Grabación habilitada', alerts_enabled: 'Alertas habilitadas', alert_threshold: 'Umbral de alertas (%)', date_format: 'Formato de fecha', kind: 'Tipo de regla', value: 'Valor', active: 'Activa', label: 'Regla', id: 'Identificador' };
  const names: Record<string, string> = { admin: 'Administrador', coordinator: 'Coordinador', viewer: 'Consulta', dmy: 'Día / mes / año', ymd: 'Año - mes - día', classroom: 'Aula', lab: 'Laboratorio', ...kinds };
  const entries = value && typeof value === 'object' ? Object.entries(value).filter(([key]) => key !== 'version') : [];
  return entries.length ? <dl className="analysis-facts">{entries.map(([key, item]) => <div key={key}><dt>{labels[key] || key}</dt><dd>{typeof item === 'boolean' ? item ? 'Sí' : 'No' : names[String(item)] || String(item)}</dd></div>)}</dl> : <p>Sin valores registrados.</p>;
}
