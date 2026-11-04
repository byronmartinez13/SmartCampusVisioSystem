import { LiveAnalysis } from './LiveAnalysis';
import { Rules, Users, AdministrativeAudit } from './Administration';
import { useState } from 'react';
import { Link, Navigate, NavLink, Outlet, Route, Routes } from 'react-router-dom';
import { Activity, Bell, Building2, CalendarDays, Clock3, FileText, GraduationCap, LayoutDashboard, LogOut, Menu, Settings as SettingsIcon, X } from 'lucide-react';
import { useAuth } from './auth';
import { Brand, Message } from './components';
import { AuthPage } from './AuthPages';
import { Dashboard } from './Dashboard';
import { Settings } from './Settings';
import { Schedule, Proposals, NewProposal, ProposalDetail } from './Scheduling';
import { Alerts, History } from './HistoryAlerts';
import { AnalysisHome, VideoUpload, VideoResult } from './VideoAnalysis';
import { Classrooms, ClassroomEditor, ClassroomDetail } from './campus/Classrooms';
import { CatalogList, CatalogEditor, CourseList, CourseEditor, CourseDetail } from './campus/Academics';

function Layout() {
  const { user, signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  if (!user) return <Navigate to="/login" replace />;
  async function logout() {
    setBusy(true); setError('');
    try { await signOut(); }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo cerrar sesión.'); }
    finally { setBusy(false); }
  }
  return <div className="app-layout">
    <button className="mobile-menu" aria-label={open ? 'Cerrar menú' : 'Abrir menú'} onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
    {open && <button className="sidebar-backdrop" aria-label="Cerrar menú lateral" onClick={() => setOpen(false)} />}
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <Link to="/dashboard" className="brand-link" aria-label="Smart Campus Vision, inicio" onClick={() => setOpen(false)}><Brand /></Link>
      <nav aria-label="Navegación principal">
        <NavLink to="/dashboard" onClick={() => setOpen(false)}><LayoutDashboard size={19} />Dashboard</NavLink>
        <NavLink to="/aulas" onClick={() => setOpen(false)}><Building2 size={19} />Aulas</NavLink>
        <NavLink to="/academico" onClick={() => setOpen(false)}><GraduationCap size={19} />Datos académicos</NavLink>
        <NavLink to="/analisis" onClick={() => setOpen(false)}><Activity size={19} />Análisis</NavLink>
        <NavLink to="/alertas" onClick={() => setOpen(false)}><Bell size={19} />Alertas</NavLink>
        <NavLink to="/historial" onClick={() => setOpen(false)}><Clock3 size={19} />Historial</NavLink>
        <NavLink to="/horarios" onClick={() => setOpen(false)}><CalendarDays size={19} />Horarios</NavLink>
        <NavLink to="/reportes" onClick={() => setOpen(false)}><FileText size={19} />Reportes</NavLink>
      </nav>
      <div className="sidebar-bottom">
        <NavLink to="/configuracion" onClick={() => setOpen(false)}><SettingsIcon size={19} />Configuración</NavLink>
        <button className="logout" disabled={busy} onClick={() => void logout()}><LogOut size={19} />{busy ? 'Cerrando sesión…' : 'Cerrar sesión'}</button>
        <div className="user-card"><span className="avatar">{user.name.trim().slice(0, 1).toUpperCase()}</span><div><strong>{user.name}</strong><span>{user.role_label}</span></div></div>
      </div>
    </aside>
    <main className="workspace">{error && <Message text={error} />}<Outlet /></main>
  </div>;
}

export function App() {
  const { loading, error, reload, user } = useAuth();
  if (loading) return <main className="connection-screen" role="status"><Brand /><p>Conectando con Smart Campus Vision…</p></main>;
  if (error) return <main className="connection-screen"><Brand /><Message text={error} /><button className="button primary" onClick={() => void reload()}>Reintentar conexión</button></main>;
  return <Routes>
    <Route path="/login" element={<AuthPage key="login" mode="login" />} />
    <Route path="/registro" element={<AuthPage key="register" mode="register" />} />
    <Route path="/recuperar" element={<AuthPage key="recover" mode="recover" />} />
    <Route path="/restablecer" element={<AuthPage key="reset" mode="reset" />} />
    <Route element={<Layout />}>
      <Route path="/administracion/reglas" element={<Rules />} />
      <Route path="/administracion/usuarios" element={<Users />} />
      <Route path="/administracion/auditoria" element={<AdministrativeAudit />} />
      <Route path="/dashboard" element={<Dashboard />} /><Route path="/configuracion" element={<Settings />} />
      <Route path="/aulas" element={<Classrooms />} />
      <Route path="/analisis" element={<AnalysisHome />} />
      <Route path="/alertas" element={<Alerts />} />
      <Route path="/historial" element={<History />} />
      <Route path="/reportes" element={<History reports />} />
      <Route path="/horarios" element={<Schedule />} />
      <Route path="/horarios/propuestas" element={<Proposals />} />
      <Route path="/horarios/nueva" element={<NewProposal />} />
      <Route path="/horarios/propuestas/:id" element={<ProposalDetail />} />
      <Route path="/analisis/en-vivo" element={<LiveAnalysis />} />
      <Route path="/analisis/video" element={<VideoUpload />} />
      <Route path="/analisis/:id" element={<VideoResult />} />
      <Route path="/aulas/nueva" element={<ClassroomEditor />} />
      <Route path="/aulas/:id" element={<ClassroomDetail />} />
      <Route path="/aulas/:id/editar" element={<ClassroomEditor />} />
      <Route path="/academico" element={<Navigate to="/academico/cursos" replace />} />
      <Route path="/academico/cursos" element={<CourseList />} />
      <Route path="/academico/cursos/nuevo" element={<CourseEditor />} />
      <Route path="/academico/cursos/:id" element={<CourseDetail />} />
      <Route path="/academico/cursos/:id/editar" element={<CourseEditor />} />
      <Route path="/academico/docentes" element={<CatalogList key="teachers" kind="teachers" />} />
      <Route path="/academico/docentes/nuevo" element={<CatalogEditor kind="teachers" />} />
      <Route path="/academico/docentes/:id/editar" element={<CatalogEditor kind="teachers" />} />
      <Route path="/academico/asignaturas" element={<CatalogList key="subjects" kind="subjects" />} />
      <Route path="/academico/asignaturas/nuevo" element={<CatalogEditor kind="subjects" />} />
      <Route path="/academico/asignaturas/:id/editar" element={<CatalogEditor kind="subjects" />} />
    </Route>
    <Route path="/" element={<Navigate to={user ? '/dashboard' : '/login'} replace />} />
    <Route path="*" element={<main className="connection-screen"><Brand /><h1>Página no encontrada</h1><Link to="/">Volver al inicio</Link></main>} />
  </Routes>;
}
