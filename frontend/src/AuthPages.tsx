import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, LockKeyhole, Mail, ShieldCheck, UserRound } from 'lucide-react';
import { api, type User } from './api';
import { useAuth } from './auth';
import { Brand, Message, PasswordField } from './components';

type Mode = 'login' | 'register' | 'recover' | 'reset';
const copy = {
  login: { badge: 'Acceso institucional', title: 'Inicio de sesión', subtitle: 'Ingresa tus datos de inicio de sesión para continuar.', button: 'Iniciar sesión' },
  register: { badge: 'Acceso institucional', title: 'Crear cuenta', subtitle: 'Ingresa tus datos para crear tu cuenta institucional.', button: 'Crear cuenta' },
  recover: { badge: 'Recuperación de cuenta', title: 'Recuperar contraseña', subtitle: 'Ingresa el correo de tu cuenta y te enviaremos un enlace para restablecerla.', button: 'Enviar enlace' },
  reset: { badge: 'Seguridad de cuenta', title: 'Nueva contraseña', subtitle: 'Crea una nueva contraseña para tu cuenta.', button: 'Restablecer contraseña' },
};

export function AuthPage({ mode }: { mode: Mode }) {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [busy, setBusy] = useState(false);
  const text = copy[mode];
  if (user && (mode === 'login' || mode === 'register')) return <Navigate to="/dashboard" replace />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    setError(''); setSuccess('');
    if (mode === 'reset' && values.password !== values.confirm) { setError('Las contraseñas no coinciden.'); return; }
    setBusy(true);
    try {
      if (mode === 'register' || mode === 'login') {
        const account = await api<User>(`/auth/${mode}/`, 'POST', values);
        setUser(account); navigate('/dashboard', { replace: true });
      } else if (mode === 'recover') {
        const result = await api<{ detail: string }>('/auth/password/recover/', 'POST', values);
        setSuccess(result.detail);
      } else {
        const result = await api<{ detail: string }>('/auth/password/reset/', 'POST', { ...values, uid: params.get('uid') || '', token: params.get('token') || '' });
        setUser(null); setSuccess(result.detail);
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'Ocurrió un error.'); }
    finally { setBusy(false); }
  }
  return <div className="auth-layout">
    <aside className="auth-visual">
      <Brand compact />
      <div className="auth-caption"><span className="eyebrow">ESPACIOS QUE CONECTAN</span>
        <h2>SMART CAMPUS VISION</h2><p>Monitoreo inteligente de<br />espacios universitarios</p>
        <span>Análisis de ocupación mediante visión computacional</span>
      </div>
    </aside>
    <main className="auth-main">
      <div className="auth-mobile-brand"><Brand /></div>
      <section className="auth-card">
        <span className="badge"><LockKeyhole size={13} /> {text.badge}</span>
        <h1>{text.title}</h1><p className="subtitle">{text.subtitle}</p>
        <form onSubmit={submit}>
          <fieldset disabled={busy || (mode === 'reset' && !!success)}>
            {mode === 'register' && <div className="field"><label htmlFor="name">Nombre</label><div className="input-icon"><UserRound size={17} /><input id="name" name="name" autoComplete="name" placeholder="Tu nombre completo" maxLength={150} required /></div></div>}
            {mode !== 'reset' && <div className="field"><label htmlFor="email">Correo electrónico</label><div className="input-icon"><Mail size={17} /><input id="email" name="email" type="email" autoComplete="email" placeholder="usuario@unemi.edu.ec" maxLength={254} required /></div></div>}
            {mode !== 'recover' && <PasswordField name="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} placeholder="Ingresa tu contraseña" minLength={mode === 'login' ? undefined : 10} />}
            {mode === 'reset' && <PasswordField label="Confirmar contraseña" name="confirm" autoComplete="new-password" minLength={10} placeholder="Repite tu contraseña" />}
            {(mode === 'register' || mode === 'reset') && <p className="password-hint"><ShieldCheck size={16} /> Usa al menos 10 caracteres y evita contraseñas comunes o completamente numéricas.</p>}
            {mode === 'login' && <div className="forgot"><Link to="/recuperar">¿Olvidaste tu contraseña?</Link></div>}
            <Message text={error} /><Message text={success} success />
            <button className="button primary full" disabled={busy}>{busy ? 'Procesando…' : text.button}<ArrowRight size={16} /></button>
          </fieldset>
        </form>
        {mode === 'login' ? <Link className="button secondary full" to="/registro">Registrarse</Link> : <Link className="button secondary full" to="/login">{mode === 'register' ? 'Iniciar sesión' : 'Volver al inicio de sesión'}</Link>}
      </section>
      <p className="auth-footer">Smart Campus Vision · Gestión de espacios académicos</p>
    </main>
  </div>;
}
