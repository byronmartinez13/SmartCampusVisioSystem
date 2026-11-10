import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowRight, Camera, CheckCircle2, Download, Film, UploadCloud } from 'lucide-react';
import { api, downloadPdf } from './api';
import { Message } from './components';
import { DeleteAnalysisButton } from './DeleteAnalysisButton';
import { dateLabel, errorText, PageHeader, ReadOnlyNotice, ResourceState, useCanManage, useResource } from './campus/shared';
import type { Classroom, Course } from './campus/types';
import type { Preferences } from './Administration';

type Sample = { frame: number; seconds: number; people: number; seats: number };
type Result = {
  people_max: number; people_mean: number; seats_max: number; sampled_frames: number; processing_seconds: number;
  video: { duration_seconds: number; fps: number; width: number; height: number };
  detector: { model: string; sha256: string; seat_semantics: string }; samples: Sample[]; peak_sample: Sample;
};
type Job = {
  options: Preferences;
  id: string; source: 'video' | 'camera'; classroom_name: string; course_name: string | null; activity: string; original_name: string;
  status: string; progress: number; error: string; result: Result | null; saved_analysis: number | null;
  capacity_snapshot: number | null; confidence: number; created_at: string;
};
const states: Record<string, string> = { queued: 'En cola', processing: 'Procesando', completed: 'Completado', failed: 'Fallido', cancelling: 'Cancelando', cancelled: 'Cancelado' };
const activities: Record<string, string> = { class: 'Clase regular', exam: 'Evaluación', practice: 'Práctica', other: 'Otra actividad' };
const active = (job: Job) => ['queued', 'processing', 'cancelling'].includes(job.status);
const referenceLabel = (result: Result) => ({ monitors: 'Monitores', chairs: 'Sillas', workstations: 'Puestos' }[result.detector.seat_semantics] ?? 'Objetos de referencia');

export function AnalysisHome() {
  const jobs = useResource<Job[]>('/video-analyses/');
  const manage = useCanManage();
  return <><PageHeader title="Análisis" subtitle="Selecciona el origen del video para evaluar la ocupación." />
    <div className="page-body">
      <div className="analysis-options">
        <section className="panel analysis-option"><Film size={38} /><h2>Video grabado</h2><p>Carga un video de un aula y consulta las detecciones, el conteo y la ocupación.</p>
          {manage ? <Link className="button primary" to="/analisis/video">Cargar video <ArrowRight size={17} /></Link> : <ReadOnlyNotice />}</section>
        <section className="panel analysis-option"><Camera size={38} /><h2>Cámara en vivo</h2><p>Analiza muestras de tu cámara local.</p>{manage ? <Link className="button primary" to="/analisis/en-vivo">Abrir cámara</Link> : <ReadOnlyNotice />}</section>
      </div>
      <section className="panel analysis-history"><div className="section-heading"><h2>Análisis recientes</h2><button className="button secondary" onClick={jobs.reload}>Actualizar</button></div>
        <ResourceState {...jobs} />
        {jobs.data?.length === 0 && <p>Aún no hay análisis. Carga un video para comenzar.</p>}
        {jobs.data && jobs.data.length > 0 && <div className="table-scroll"><table><thead><tr><th>Video / aula</th><th>Fecha</th><th>Estado</th><th>Resultado</th></tr></thead>
          <tbody>{jobs.data.map(job => <tr key={job.id}><td><Link to={`/analisis/${job.id}`}>{job.original_name}</Link><small className="table-subtext">{job.classroom_name}</small></td><td>{dateLabel(job.created_at)}</td><td>{states[job.status]}</td><td>{job.saved_analysis ? 'Guardado' : 'Sin guardar resumen'}</td></tr>)}</tbody></table></div>}
        <p className="small-muted">Se muestran los últimos 100 análisis. El procesamiento continúa aunque salgas de esta página.</p>
      </section>
    </div></>;
}

export function VideoUpload() {
  const preferences = useResource<Preferences>('/settings/');
  const classrooms = useResource<Classroom[]>('/classrooms/');
  const courses = useResource<Course[]>('/courses/');
  const [classroom, setClassroom] = useState('');
  const [course, setCourse] = useState('');
  const [activity, setActivity] = useState('class');
  const [confidence, setConfidence] = useState('.5');
  useEffect(() => { if (preferences.data) setConfidence(String(preferences.data.confidence)); }, [preferences.data]);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const manage = useCanManage();
  useEffect(() => {
    if (!file) { setPreview(''); return; }
    const url = URL.createObjectURL(file); setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  function choose(value?: File) {
    setError('');
    if (!value) return;
    if (!/\.(mp4|avi)$/i.test(value.name) || value.size === 0 || value.size > 250 * 1024 * 1024) {
      setError('Selecciona un archivo MP4 o AVI de hasta 250 MB.'); return;
    }
    setFile(value);
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file || !classroom) return;
    const data = new FormData();
    data.append('video', file); data.append('classroom', classroom); data.append('activity', activity); data.append('confidence', confidence);
    if (course) data.append('course', course);
    setBusy(true); setError('');
    try { const job = await api<Job>('/video-analyses/', 'POST', data); navigate(`/analisis/${job.id}`); }
    catch (e) { setError(errorText(e)); }
    finally { setBusy(false); }
  }
  const room = classrooms.data?.find(r => String(r.id) === classroom);
  return <><PageHeader title="Análisis de video" subtitle="Análisis › Video grabado"><Link to="/analisis" className="button secondary">Volver</Link></PageHeader>
    <div className="page-body"><ResourceState {...classrooms} /><ResourceState {...courses} />
      {!manage ? <ReadOnlyNotice /> : <form className="analysis-columns" onSubmit={e => void submit(e)}>
        <section className="panel analysis-config"><h2>Configuración</h2><p className="small-muted">Define el contexto del video antes de iniciar el análisis.</p>
          <div className="field"><label htmlFor="analysis-classroom">Aula o laboratorio</label><select required id="analysis-classroom" value={classroom} onChange={e => setClassroom(e.target.value)} disabled={busy}><option value="">Selecciona un aula</option>{classrooms.data?.filter(r => r.active).map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select></div>
          {classrooms.data?.filter(r => r.active).length === 0 && <p><Link to="/aulas/nueva">Crea un aula</Link> antes de analizar.</p>}
          <div className="field"><label htmlFor="analysis-course">Curso / asignatura</label><select id="analysis-course" value={course} onChange={e => setCourse(e.target.value)} disabled={busy}><option value="">Sin curso asociado</option>{courses.data?.filter(c => c.active).map(c => <option key={c.id} value={c.id}>{c.code} · {c.name}</option>)}</select></div>
          <div className="field"><label htmlFor="analysis-activity">Tipo de actividad</label><select id="analysis-activity" value={activity} onChange={e => setActivity(e.target.value)} disabled={busy}>{Object.entries(activities).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
          <div className="field"><label htmlFor="confidence">Confianza mínima del detector</label><select id="confidence" aria-describedby="confidence-help" value={confidence} onChange={e => setConfidence(e.target.value)} disabled={busy}>{['.25', '.5', '.7', '.9'].map(v => <option key={v} value={v}>{Number(v) * 100}%{v === '.5' ? ' · valor inicial' : ''}</option>)}</select><p id="confidence-help" className="small-muted">Este valor filtra detecciones; aumentarlo puede descartar personas visibles. Un 90% no significa un 90% de precisión. Empieza con 50% y compara los conteos con el video.</p></div>
          <label className="video-dropzone" onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (!busy) choose(e.dataTransfer.files[0]); }}>
            <UploadCloud size={30} /><strong>{file ? file.name : 'Cargar video'}</strong><span>Arrastra un video o selecciona un archivo</span><small>MP4 o AVI · hasta 250 MB · máximo 10 minutos</small>
            <input aria-label="Archivo de video" type="file" accept=".mp4,.avi" disabled={busy} onChange={e => choose(e.target.files?.[0])} />
          </label>
        </section>
        <section className="panel analysis-summary"><h2>Resumen del análisis</h2><p className="small-muted">Revisa los datos configurados antes de continuar.</p>
          <dl className="analysis-facts"><div><dt>Aula o laboratorio</dt><dd>{room?.name ?? 'Sin seleccionar'}</dd></div><div><dt>Curso</dt><dd>{courses.data?.find(c => String(c.id) === course)?.name ?? 'Sin curso asociado'}</dd></div><div><dt>Actividad</dt><dd>{activities[activity]}</dd></div><div><dt>Archivo</dt><dd>{file ? `${file.name} · ${(file.size / 1048576).toFixed(1)} MB` : 'Sin archivo'}</dd></div><div><dt>Capacidad validada</dt><dd>{room?.validated_capacity ?? 'Pendiente'}</dd></div></dl>
          {preview && <video className="video-local-preview" src={preview} controls preload="metadata" />}
          <p className="small-muted">El detector inicial cuenta personas y monitores visibles. Un monitor detectado no garantiza un puesto utilizable: puede haber pantallas compartidas, varios monitores por puesto o equipos fuera de cámara. La ocupación se compara con la capacidad validada del aula.</p>
          <Message text={error} /><button className="button primary analysis-submit" disabled={!file || !classroom || busy} type="submit">{busy ? 'Subiendo video…' : 'Iniciar análisis'}<ArrowRight size={17} /></button>
        </section>
      </form>}
    </div></>;
}

export function VideoResult() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (job?.status !== 'completed' || !job.options?.auto_pdf || sessionStorage.getItem(`pdf-${job.id}`)) return;
    sessionStorage.setItem(`pdf-${job.id}`, 'requested');
    void downloadPdf(`/video-analyses/${job.id}/report/`, `analisis-${job.id}.pdf`).catch(e => {
      sessionStorage.removeItem(`pdf-${job.id}`); setError(errorText(e));
    });
  }, [job]);
  const manage = useCanManage();
  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const value = await api<Job>(`/video-analyses/${id}/`);
        if (disposed) return;
        setJob(value); setError('');
        if (active(value)) timer = setTimeout(() => void refresh(), 2000);
      } catch (e) { if (!disposed) setError(errorText(e)); }
    }
    void refresh();
    return () => { disposed = true; clearTimeout(timer); };
  }, [id, revision]);
  async function action(name: string) {
    setBusy(true); setError('');
    try { setJob(await api<Job>(`/video-analyses/${id}/${name}/`, 'POST')); setRevision(r => r + 1); }
    catch (e) { setError(errorText(e)); }
    finally { setBusy(false); }
  }
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(job, null, 2)], { type: 'application/json' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = `analisis-${id}.json`; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const result = job?.result;
  const capacity = job?.capacity_snapshot;
  const occupancy = result && capacity != null && capacity > 0 ? (result.people_max / capacity * 100).toFixed(1) : null;
  return <><PageHeader title={job?.status === 'completed' ? 'Resultado del análisis' : 'Procesamiento de video'} subtitle={job ? `${job.classroom_name} · ${job.original_name}` : 'Consultando análisis…'}><Link to="/analisis" className="button secondary">Ver análisis</Link></PageHeader>
    <div className="page-body"><Message text={error} />{error && <button className="button secondary" onClick={() => setRevision(r => r + 1)}>Reintentar consulta</button>}
      {!job && !error && <p role="status">Cargando…</p>}
      {job && <>
        {manage && !active(job) && <div className="analysis-actions"><DeleteAnalysisButton id={job.id} name={job.original_name} onError={setError} onDeleted={() => navigate('/reportes')} /></div>}
        <section className="panel analysis-progress"><div className="section-heading"><h2>{states[job.status]}</h2><strong>{job.progress}%</strong></div><progress max={100} value={job.progress} aria-label="Progreso del análisis" />
          {active(job) && <p role="status">{job.status === 'queued' ? 'Esperando al servicio de visión.' : job.status === 'cancelling' ? 'Esperando confirmación de cancelación.' : 'Evaluando fotogramas. Puedes volver a esta página más tarde.'}</p>}
          <Message text={job.error} />
          {manage && active(job) && <button className="button secondary" disabled={busy || job.status === 'cancelling'} onClick={() => void action('cancel')}>Cancelar análisis</button>}
          {manage && job.source !== 'camera' && ['failed', 'cancelled'].includes(job.status) && <button className="button primary" disabled={busy} onClick={() => void action('retry')}>Reintentar análisis</button>}
        </section>
        {result && job.status === 'completed' && <>
          <p className="read-only-note">Disponibilidad estimada en este análisis: <strong>{capacity == null ? 'No disponible: falta validar capacidad' : `${Math.max(0, capacity - result.people_max)} puestos`}</strong>. Se calcula con la capacidad validada al cargar y el máximo de personas detectadas. No identifica puestos libres concretos ni refleja disponibilidad en tiempo real.</p>
          {result.people_max === 0 && <p className="read-only-note" role="status">No se detectaron personas por encima del umbral de confianza del {job.confidence * 100}%. Esto no confirma que el aula esté vacía. Revisa el video y, si hay personas visibles, realiza un nuevo análisis con un umbral menor. El modelo también puede omitir personas por distancia u oclusión.</p>}
          <div className="analysis-metrics">
            {[['Personas · máximo visible', result.people_max], [`${referenceLabel(result)} · máximo detectado`, result.seats_max], ['Capacidad validada', capacity ?? 'Pendiente'], ['Ocupación máxima estimada', occupancy === null ? 'No disponible' : `${occupancy}%`]].map(([label, value]) => <div className="panel" key={label}><span>{label}</span><strong>{value}</strong></div>)}
          </div>
          <div className="analysis-columns"><section className="panel"><h2>Fotograma con más personas</h2>{job.source === 'camera' ? <p>Las muestras de la cámara no se conservan como imágenes.</p> : <img className="analysis-preview" src={`/api/video-analyses/${id}/preview/`} alt={`Fotograma del video con las detecciones de personas y ${referenceLabel(result).toLowerCase()} marcadas`} />}<p className="small-muted">Instante {result.peak_sample.seconds} s · azul: personas · verde: {referenceLabel(result).toLowerCase()}.</p></section>
            <section className="panel"><h2>Detalle del resultado</h2><dl className="analysis-facts"><div><dt>Modelo</dt><dd>{result.detector.model}</dd></div><div><dt>Confianza mínima</dt><dd>{job.confidence * 100}%</dd></div><div><dt>Fotogramas evaluados</dt><dd>{result.sampled_frames}</dd></div><div><dt>Promedio de personas</dt><dd>{result.people_mean}</dd></div><div><dt>Duración del video</dt><dd>{result.video.duration_seconds} s</dd></div><div><dt>Tiempo de procesamiento</dt><dd>{result.processing_seconds} s</dd></div></dl>
              <p className="read-only-note">{capacity == null ? 'Valida la capacidad del aula antes de un próximo análisis para obtener ocupación.' : job.options?.alerts_enabled === false ? 'Las alertas estaban desactivadas al iniciar este análisis.' : result.people_max * 100 > capacity * (job.options?.alert_threshold ?? 100) ? 'El máximo detectado supera el umbral de alerta configurado. Al guardar se registra una alerta para revisión.' : 'El máximo detectado no supera el umbral de alerta configurado.'}</p>
              {result.detector.seat_semantics === 'monitors' && <p className="read-only-note">Los monitores son una referencia visual para validar puestos, no un conteo de puestos libres. El modelo general usa la clase «tv», que también puede detectar televisores. Para estimar puestos disponibles necesitamos capacidad validada y correspondencia entre equipos y puestos.</p>}
              <p className="small-muted">Alertas de este análisis: {job.options?.alerts_enabled === false ? 'desactivadas' : `se crean al guardar si se supera el ${job.options?.alert_threshold ?? 100}% de la capacidad validada`}. Los cambios de configuración posteriores no alteran esta condición.</p>
              <p className="small-muted">{job.source === 'camera' ? 'Se evalúa una muestra por solicitud; la frecuencia depende del equipo y la red.' : 'Se evalúan aproximadamente 2 fotogramas por segundo.'} Son detecciones visibles por fotograma; no representan personas únicas ni una precisión validada. Los máximos de {referenceLabel(result).toLowerCase()} y personas pueden corresponder a instantes distintos.</p>
            </section></div>
          <section className="panel analysis-history"><h2>Conteos por fotograma</h2><div className="sample-scroll"><table><thead><tr><th>Tiempo (s)</th><th>Personas</th><th>{referenceLabel(result)} detectados</th></tr></thead><tbody>{result.samples.map(s => <tr key={s.frame}><td>{s.seconds}</td><td>{s.people}</td><td>{s.seats}</td></tr>)}</tbody></table></div></section>
          <div className="analysis-actions">{job.saved_analysis ? <p className="saved-result"><CheckCircle2 size={19} />Resultado guardado en el dashboard y la actividad del aula.</p> : manage && <button className="button primary" disabled={busy} onClick={() => void action('save-result')}>Guardar resultado</button>}<button className="button secondary" disabled={busy} onClick={() => { setBusy(true); setError(''); void downloadPdf(`/video-analyses/${id}/report/`, `analisis-${id}.pdf`).catch(e => setError(errorText(e))).finally(() => setBusy(false)); }}>Descargar PDF</button><button className="button secondary" onClick={download}><Download size={17} />Descargar datos JSON</button>{manage && <Link to="/analisis/video" className="button secondary">Nuevo análisis</Link>}</div>
        </>}
      </>}
    </div></>;
}
