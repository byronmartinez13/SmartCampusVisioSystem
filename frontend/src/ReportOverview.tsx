import { ResourceState, useResource } from './campus/shared';

type Group = { period: string; analyses: number; people_max: number; occupancy_mean: number | null };
type Summary = { analyses: number; people_max: number | null; occupancy_mean: number | null; without_capacity: number; over_capacity: number; days: Group[]; hours: Group[] };

export function ReportOverview({ params }: { params: string }) {
  const resource = useResource<Summary>(`/analysis-history/summary/?${params}`);
  const data = resource.data;
  return <section className="panel settings-panel"><h2>Resumen del período</h2><ResourceState {...resource} />{data && <>
    <dl className="analysis-facts"><div><dt>Análisis completados</dt><dd>{data.analyses}</dd></div><div><dt>Máximo de personas en una muestra</dt><dd>{data.people_max ?? 'No disponible'}</dd></div><div><dt>Ocupación media con capacidad positiva</dt><dd>{data.occupancy_mean === null ? 'No disponible' : `${data.occupancy_mean}%`}</dd></div><div><dt>Análisis sobre capacidad</dt><dd>{data.over_capacity}</dd></div><div><dt>Sin capacidad positiva</dt><dd>{data.without_capacity}</dd></div></dl>
    <h3>Evolución por fecha</h3>{data.days.length ? <div className="table-wrap"><table><thead><tr><th>Fecha</th><th>Análisis</th><th>Máximo de personas</th><th>Ocupación media</th></tr></thead><tbody>{data.days.map(g => <tr key={g.period}><td>{g.period}</td><td>{g.analyses}</td><td>{g.people_max}</td><td>{g.occupancy_mean === null ? 'No disponible' : `${g.occupancy_mean}%`}</td></tr>)}</tbody></table></div> : <p>No hay análisis completados con estos filtros.</p>}
    <h3>Horas con mayor máximo observado</h3>{data.hours.slice(0, 5).map(g => <p key={g.period}>{g.period} · {g.people_max} personas como máximo · {g.analyses} análisis</p>)}
    <p className="small-muted">Fechas y horas de carga del video o inicio de cámara, en America/Guayaquil. No indican la hora de grabación de un archivo ni personas únicas. Los promedios son por análisis; no son promedios ponderados por duración.</p>
  </>}</section>;
}
