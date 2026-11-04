import { useEffect, useState } from 'react';
import { Activity, BarChart3, Building2, RefreshCw, TriangleAlert } from 'lucide-react';
import { api, type DashboardData } from './api';
import { Message } from './components';

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  async function load() {
    setLoading(true); setError('');
    try { setData(await api<DashboardData>('/dashboard/')); }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo cargar el resumen.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  const hasOccupancy = data?.occupancy.some(item => item.percent !== null);
  const scale = Math.max(100, ...data?.occupancy.map(item => item.percent || 0) || []);
  return <>
    <header className="page-header"><div><h1>Dashboard</h1><p>Una visión general de tus espacios académicos.</p></div>
      <button className="button secondary refresh" onClick={() => void load()} disabled={loading}><RefreshCw size={16} className={loading ? 'spin' : ''} />Actualizar</button>
    </header>
    <div className="page-body">
      <div className="section-heading"><span />RESUMEN GENERAL</div>
      <Message text={error} />
      <div className="stats-grid" aria-busy={loading}>
        {[
          { label: 'Aulas activas', value: data?.classrooms, Icon: Building2, color: 'blue' },
          { label: 'Aulas analizadas', value: data?.analyzed_classrooms, Icon: Activity, color: 'teal' },
          { label: 'Conflictos abiertos', value: data?.open_alerts, Icon: TriangleAlert, color: 'amber' },
        ].map(({ label, value, Icon, color }) => <section className="stat-card" key={label}><span className={`stat-icon ${color}`}><Icon size={29} strokeWidth={1.7} /></span><div><strong>{value ?? '—'}</strong><p>{label}</p></div></section>)}
      </div>
      <section className="panel chart-panel">
        <div className="panel-heading"><h2><BarChart3 size={20} />Ocupación de aulas</h2><span className="small-muted">Semana actual · promedio diario</span></div>
        {loading && !data ? <div className="empty-state" role="status">Cargando información…</div> :
          !hasOccupancy ? <div className="empty-state"><span className="empty-icon"><BarChart3 size={36} strokeWidth={1.4} /></span>
            <h3>{error ? 'No se pudo cargar la ocupación' : 'Aún no hay análisis esta semana'}</h3>
            <p>{error ? 'Utiliza Actualizar para volver a intentarlo.' : 'Cuando se registren análisis con capacidad conocida, aquí verás la ocupación de las aulas.'}</p>
            {!error && <span className="empty-tag">Sin datos registrados</span>}
          </div> :
          <div className="chart" aria-label="Ocupación promedio por día">
            {data?.occupancy.map((item, i) => <div className="chart-column" key={item.date}>
              <span>{item.percent === null ? 'Sin datos' : `${item.percent}%`}</span>
              <div className="bar-track"><div className={`bar ${i % 2 ? 'teal-bar' : ''}`} style={{ height: `${(item.percent || 0) / scale * 100}%` }} /></div>
              <span>{['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][i]}</span>
            </div>)}
          </div>}
      </section>
      <div className="dashboard-note"><span className="status-dot" />Información obtenida de los registros del sistema.</div>
    </div>
  </>;
}
