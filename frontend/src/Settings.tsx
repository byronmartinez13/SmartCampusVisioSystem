import { useState, type FormEvent } from 'react';
import { Save, ShieldCheck } from 'lucide-react';
import { useAuth } from './auth';
import { api, type User } from './api';
import { Message, PasswordField } from './components';
import { GeneralSettings } from './Administration';

export function Settings() {
  const { user, setUser } = useAuth();
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  async function save(event: FormEvent<HTMLFormElement>, password = false) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    setError(''); setMessage('');
    if (password && data.password !== data.confirm) { setError('Las contraseñas no coinciden.'); return; }
    setBusy(true);
    try {
      if (password) {
        await api('/auth/password/change/', 'POST', data);
        setMessage('Contraseña actualizada correctamente.'); form.reset();
      } else {
        setUser(await api<User>('/auth/me/', 'PATCH', data)); setMessage('Perfil actualizado correctamente.');
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudieron guardar los cambios.'); }
    finally { setBusy(false); }
  }
  return <><header className="page-header"><div><h1>Configuración</h1><p>Tu perfil y la seguridad de tu cuenta.</p></div></header>
    <div className="page-body settings-body">
      <Message text={error} /><Message text={message} success /><GeneralSettings />
      <section className="panel settings-panel"><h2>Cuenta</h2>
        <form onSubmit={event => void save(event)}><fieldset disabled={busy}>
          <div className="profile-fields"><div className="field"><label htmlFor="profile-name">Nombre</label><input id="profile-name" name="name" defaultValue={user?.name} maxLength={150} required /></div>
            <div className="field"><label htmlFor="profile-email">Correo electrónico</label><input id="profile-email" value={user?.email || ''} readOnly /></div>
            <div className="field"><label htmlFor="profile-role">Rol de acceso</label><input id="profile-role" value={user?.role_label || ''} readOnly /></div></div>
          <button className="button primary" disabled={busy}><Save size={16} />Guardar perfil</button>
        </fieldset></form>
      </section>
      <section className="panel settings-panel password-panel"><h2><ShieldCheck size={22} />Cambiar contraseña</h2><p className="small-muted">Usa al menos 10 caracteres. Las otras sesiones se cerrarán al cambiarla.</p>
        <form onSubmit={event => void save(event, true)}><fieldset disabled={busy}>
          <PasswordField name="current_password" label="Contraseña actual" autoComplete="current-password" />
          <PasswordField name="password" label="Nueva contraseña" autoComplete="new-password" minLength={10} />
          <PasswordField name="confirm" label="Confirmar contraseña" autoComplete="new-password" minLength={10} />
          <button className="button primary" disabled={busy}>Actualizar contraseña</button>
        </fieldset></form>
      </section>
    </div></>;
}
