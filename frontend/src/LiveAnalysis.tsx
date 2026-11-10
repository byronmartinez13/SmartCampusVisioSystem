import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { LiveMonitor, useLiveBroadcast } from './LiveMonitor';
import { api } from './api';
import { Message } from './components';
import { errorText, PageHeader, ReadOnlyNotice, ResourceState, useCanManage, useResource } from './campus/shared';
import type { Classroom, Course } from './campus/types';
import type { Preferences } from './Administration';

type Detection = { people: number; seats: number; samples: number; people_max: number; width: number; height: number;
  detector: { seat_semantics: string }; boxes: { kind: string; xyxy: number[] }[] };
type Session = { id: string; capacity_snapshot: number | null; status: string; options: Preferences };

export function LiveAnalysis() {
  const [params] = useSearchParams();
  const watch = params.get('monitor');
  return watch ? <LiveMonitor id={watch} /> : <CameraCapture />;
}

function CameraCapture() {
  const rooms = useResource<Classroom[]>('/classrooms/');
  const courses = useResource<Course[]>('/courses/');
  const preferences = useResource<Preferences>('/settings/');
  const manage = useCanManage();
  const [room, setRoom] = useState('');
  const [confidence, setConfidence] = useState('0.5');
  const [activity, setActivity] = useState('class');
  const [course, setCourse] = useState('');
  const [facing, setFacing] = useState('environment');
  const [copied, setCopied] = useState(false);
  const [record, setRecord] = useState(false);
  const [recordingUrl, setRecordingUrl] = useState('');
  const recording = useRef<MediaRecorder | null>(null);
  const recordingObjectUrl = useRef('');
  useEffect(() => { if (preferences.data) setConfidence(String(preferences.data.confidence)); }, [preferences.data]);
  const [session, setSession] = useState<Session | null>(null);
  const [latest, setLatest] = useState<Detection | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [running, setRunning] = useState(false);
  const [sampleMs, setSampleMs] = useState<number | null>(null);
  const csrf = useRef('');
  const video = useRef<HTMLVideoElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const active = useRef(false);
  const mounted = useRef(true);
  const current = useRef<Session | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const broadcast = useLiveBroadcast(running ? session?.id ?? null : null, stream);

  function release() {
    active.current = false;
    clearTimeout(timer.current);
    if (recording.current && recording.current.state !== 'inactive') recording.current.stop();
    stream.current?.getTracks().forEach(track => track.stop());
    stream.current = null;
  }
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false; release();
      if (recordingObjectUrl.current) URL.revokeObjectURL(recordingObjectUrl.current);
      if (current.current?.status === 'processing') {
        const id = current.current.id;
        void api(`/live-sessions/${id}/stop/`, 'POST').catch(() => undefined);
      }
    };
  }, []);

  async function sample(id: string) {
    if (!active.current || !video.current || !canvas.current) return;
    const started = performance.now();
    const image = document.createElement('canvas');
    image.width = video.current.videoWidth; image.height = video.current.videoHeight;
    const context = image.getContext('2d');
    if (!context || !image.width) { timer.current = setTimeout(() => void sample(id), 500); return; }
    context.drawImage(video.current, 0, 0);
    try {
      const blob = await new Promise<Blob | null>(resolve => image.toBlob(resolve, 'image/jpeg', .8));
      if (!blob || !active.current) return;
      const form = new FormData(); form.append('image', blob, 'frame.jpg');
      const result = await api<Detection>(`/live-sessions/${id}/frame/`, 'POST', form, csrf.current);
      if (!active.current || !canvas.current) return;
      setLatest(result); setError(''); setSampleMs(Math.round(performance.now() - started));
      const output = canvas.current; output.width = image.width; output.height = image.height;
      const drawing = output.getContext('2d')!; drawing.drawImage(image, 0, 0);
      drawing.lineWidth = 3;
      result.boxes.forEach(box => {
        drawing.strokeStyle = box.kind === 'person' ? '#3b82f6' : '#14b8a6';
        const [x1, y1, x2, y2] = box.xyxy; drawing.strokeRect(x1, y1, x2 - x1, y2 - y1);
      });
    } catch (e) {
      if (mounted.current && active.current) setError(errorText(e));
      // Stop automatic retries: the user can stop and retain successful samples.
      release();
      if (mounted.current) setRunning(false);
      return;
    }
    // One request at a time; target at most 5 samples/s without buffering old frames.
    if (active.current) timer.current = setTimeout(() => void sample(id), Math.max(0, 200 - (performance.now() - started)));
  }

  async function start() {
    setBusy(true); setError(''); setLatest(null); setSampleMs(null);
    if (recordingObjectUrl.current) URL.revokeObjectURL(recordingObjectUrl.current);
    setRecordingUrl('');
    try {
      csrf.current = (await api<{ csrfToken: string }>('/auth/csrf/')).csrfToken;
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('La cámara requiere localhost o HTTPS y un navegador compatible.');
      const media = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: facing }, width: { ideal: 960, max: 1280 }, height: { ideal: 540, max: 720 } }, audio: false });
      if (!mounted.current) { media.getTracks().forEach(track => track.stop()); return; }
      stream.current = media;
      video.current!.srcObject = media;
      await video.current!.play();
      const created = await api<Session>('/live-sessions/', 'POST', { classroom: Number(room), confidence: Number(confidence), activity, course: course ? Number(course) : null }, csrf.current);
      current.current = created;
      if (!mounted.current) { release(); void api(`/live-sessions/${created.id}/stop/`, 'POST'); return; }
      setSession(created); active.current = true; setRunning(true);
      if (record && created.options.record_live) {
        if (typeof MediaRecorder === 'undefined' || !MediaRecorder.isTypeSupported('video/webm')) {
          setError('Este navegador no permite grabar WebM. El análisis continúa sin grabación.');
        } else {
          const chunks: Blob[] = []; let size = 0;
          const recorder = new MediaRecorder(media, { mimeType: 'video/webm', videoBitsPerSecond: 1000000 });
          recording.current = recorder;
          recorder.ondataavailable = e => {
            if (e.data.size) { chunks.push(e.data); size += e.data.size; }
            if (size >= 100 * 1024 * 1024 && recorder.state !== 'inactive') recorder.stop();
          };
          recorder.onstop = () => {
            if (!mounted.current || !chunks.length) return;
            const url = URL.createObjectURL(new Blob(chunks, { type: 'video/webm' }));
            recordingObjectUrl.current = url; setRecordingUrl(url);
          };
          recorder.start(1000);
        }
      }
      media.getVideoTracks()[0].addEventListener('ended', () => {
        release(); if (mounted.current) { setRunning(false); setError('La cámara se desconectó. Detén la sesión para conservar las muestras.'); }
      });
      void sample(created.id);
    } catch (e) { release(); if (mounted.current) setError(errorText(e)); }
    finally { if (mounted.current) setBusy(false); }
  }

  async function stop() {
    release(); setRunning(false); setBusy(true); setError('');
    try {
      const stopped = await api<Session>(`/live-sessions/${session!.id}/stop/`, 'POST');
      current.current = stopped; setSession(stopped);
    } catch (e) { setError(errorText(e)); }
    finally { setBusy(false); }
  }

  const open = session?.status === 'processing';
  const capacity = session?.capacity_snapshot;
  return <><PageHeader title="Análisis en vivo" subtitle="Una cámara local. Se analizan muestras sucesivas; los fotogramas no se almacenan." />
    <div className="page-body"><Message text={error} /><ResourceState {...rooms} />
      {!manage ? <ReadOnlyNotice /> : <>
      <section className="panel settings-panel"><h2>Configurar sesión</h2>
        <fieldset disabled={busy || !!open}><div className="field"><label htmlFor="live-room">Aula</label><select id="live-room" value={room} onChange={e => setRoom(e.target.value)}><option value="">Selecciona un aula</option>{rooms.data?.filter(r => r.active).map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select></div>
        <div className="field"><label htmlFor="live-facing">Cámara preferida</label><select id="live-facing" value={facing} onChange={e => setFacing(e.target.value)}><option value="environment">Trasera (teléfono)</option><option value="user">Frontal / webcam</option></select><p className="small-muted">La selección depende de las cámaras disponibles en el dispositivo. Detén la sesión antes de cambiarla.</p></div>
        <div className="field"><label htmlFor="live-activity">Actividad</label><select id="live-activity" value={activity} onChange={e => setActivity(e.target.value)}><option value="class">Clase</option><option value="exam">Evaluación</option><option value="practice">Práctica</option><option value="other">Otra</option></select></div>
        <div className="field"><label htmlFor="live-course">Curso (opcional)</label><select id="live-course" value={course} onChange={e => setCourse(e.target.value)}><option value="">Sin curso</option>{courses.data?.filter(c => c.active).map(c => <option key={c.id} value={c.id}>{c.code} - {c.name}</option>)}</select></div><ResourceState {...courses} />
        {preferences.data?.record_live && <label className="setting-check"><input type="checkbox" checked={record} onChange={e => setRecord(e.target.checked)} /> Grabar cámara para descargar localmente (WebM, hasta 100 MB). Descarga antes de salir de esta página.</label>}
        <div className="field"><label htmlFor="live-confidence">Confianza mínima</label><input id="live-confidence" type="number" min="0.1" max="0.95" step="0.05" value={confidence} onChange={e => setConfidence(e.target.value)} /></div>
        <button className="button primary" disabled={!room || busy || !!open || Number(confidence) < .1 || Number(confidence) > .95} onClick={() => void start()}>Iniciar cámara</button></fieldset>
        {open && <button className="button secondary" disabled={busy} onClick={() => void stop()}>Detener sesión</button>}
        <p className="small-muted">Hasta 10 minutos o 1000 muestras. El navegador solicitará permiso para la cámara. Requiere el servicio de visión en ejecución.</p>
      </section>
      <section className="panel settings-panel"><h2>{running ? 'Cámara activa' : 'Cámara detenida'}</h2>
        {running && session && <div className="field"><label htmlFor="live-monitor-link">Ver video y conteos en la laptop</label><input id="live-monitor-link" readOnly value={`${window.location.origin}/analisis/en-vivo?monitor=${session.id}`} onFocus={e => e.target.select()} /><button className="button secondary" onClick={() => { void navigator.clipboard?.writeText(`${window.location.origin}/analisis/en-vivo?monitor=${session.id}`).then(() => setCopied(true)).catch(() => setError('Selecciona el enlace y cópialo manualmente.')); }}>{copied ? 'Enlace copiado' : 'Copiar enlace del monitor'}</button><p className="small-muted">Abre el enlace en la laptop con tu misma cuenta. Mantén esta página abierta y ambos equipos en el mismo Wi-Fi. Un monitor a la vez. {broadcast}</p></div>}
        {running && !latest && <p role="status">Preparando la primera detección. La carga inicial del modelo puede tardar hasta dos minutos.</p>}
        <video ref={video} autoPlay muted playsInline style={{ width: '100%', maxWidth: 960, display: running ? 'block' : 'none' }} />
        <h3>Última muestra analizada</h3>{sampleMs !== null && <p className="small-muted">Tiempo de la última muestra (red y análisis): {sampleMs} ms. La frecuencia real depende de la conexión y del servidor.</p>}<canvas ref={canvas} style={{ width: '100%', maxWidth: 960, display: latest ? 'block' : 'none' }} />
        {latest && <><p role="status">Personas: {latest.people} · Máximo de sesión: {latest.people_max} · Muestras: {latest.samples}</p>
        <p>Ocupación de la última muestra: {capacity ? `${(latest.people / capacity * 100).toFixed(1)}%` : 'No disponible: falta capacidad validada al iniciar.'}</p>
        {capacity != null && latest.people > capacity && <p role="alert">Sobreocupación estimada. Revisa visualmente el conteo.</p>}</>}
        <p className="small-muted">Azul: personas. Verde: objetos de referencia. Los conteos pueden omitir personas por distancia u oclusión. La imagen analizada tiene retraso respecto a la cámara y no identifica personas únicas.</p>
      </section>
      {recordingUrl && <p><a className="button secondary" href={recordingUrl} download={`camara-${session?.id}.webm`}>Descargar grabación WebM</a></p>}
      {session && !open && <section className="panel settings-panel"><h2>Sesión {session.status === 'completed' ? 'completada' : 'sin muestras'}</h2>{session.status === 'completed' && <Link className="button primary" to={`/analisis/${session.id}`}>Ver resultado y guardar resumen</Link>}</section>}
      </>}
    </div></>;
}
