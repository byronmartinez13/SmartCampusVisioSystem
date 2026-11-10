import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from './api';
import { Message } from './components';
import { errorText, PageHeader } from './campus/shared';

type Signal = { viewer: string; sdp: string };
type State = {
  status: string; capacity: number | null; offer: Signal | null; answer: Signal | null;
  latest: { people: number; people_max: number; samples: number; received_at: string } | null;
};

async function gatherIce(peer: RTCPeerConnection) {
  if (peer.iceGatheringState === 'complete') return;
  await new Promise<void>(resolve => {
    const done = () => { clearTimeout(timeout); peer.removeEventListener('icegatheringstatechange', check); resolve(); };
    const check = () => { if (peer.iceGatheringState === 'complete') done(); };
    const timeout = setTimeout(done, 6000);
    peer.addEventListener('icegatheringstatechange', check);
    check();
  });
}

// Host candidates only: no external relay or video storage. Both devices need
// a network that permits direct connections (guest Wi-Fi may isolate clients).
export function useLiveBroadcast(id: string | null, media: React.RefObject<MediaStream | null>) {
  const [status, setStatus] = useState('');
  useEffect(() => {
    if (!id) { setStatus(''); return; }
    let closed = false;
    let timer: ReturnType<typeof setTimeout>;
    let peer: RTCPeerConnection | null = null;
    let viewer = '';
    const poll = async () => {
      try {
        const state = await api<State>(`/live-sessions/${id}/monitor/`);
        if (closed) return;
        if (state.offer && state.offer.viewer !== viewer && media.current) {
          peer?.close();
          const connection = new RTCPeerConnection({ iceServers: [] });
          peer = connection; viewer = state.offer.viewer;
          setStatus('Conectando la laptop…');
          connection.onconnectionstatechange = () => {
            if (!closed) setStatus(connection.connectionState === 'connected' ? 'Video conectado a la laptop.'
              : connection.connectionState === 'failed' ? 'No se pudo conectar. Comprueba el Wi-Fi y reconecta desde la laptop.' : 'Conectando la laptop…');
          };
          media.current.getVideoTracks().forEach(track => connection.addTrack(track, media.current!));
          await connection.setRemoteDescription({ type: 'offer', sdp: state.offer.sdp });
          await connection.setLocalDescription(await connection.createAnswer());
          await gatherIce(connection);
          if (closed) return;
          await api(`/live-sessions/${id}/monitor/`, 'POST', {
            kind: 'answer', viewer, sdp: connection.localDescription!.sdp,
          });
        }
      } catch (e) { if (!closed) setStatus(errorText(e)); }
      if (!closed) timer = setTimeout(() => void poll(), 1500);
    };
    setStatus('Abre el enlace del monitor en la laptop.');
    void poll();
    return () => { closed = true; clearTimeout(timer); peer?.close(); };
  }, [id, media]);
  return status;
}

export function LiveMonitor({ id }: { id: string }) {
  const video = useRef<HTMLVideoElement>(null);
  const [state, setState] = useState<State | null>(null);
  const [error, setError] = useState('');
  const [connection, setConnection] = useState('Conectando…');
  const [attempt, setAttempt] = useState(0);
  const [playBlocked, setPlayBlocked] = useState(false);
  useEffect(() => {
    let closed = false;
    let timer: ReturnType<typeof setTimeout>;
    const peer = new RTCPeerConnection({ iceServers: [] });
    const viewer = crypto.randomUUID();
    let answered = false;
    setError(''); setState(null); setConnection('Conectando…');
    peer.ontrack = event => {
      if (!closed && video.current) {
        video.current.srcObject = event.streams[0] ?? new MediaStream([event.track]);
        void video.current.play().catch(() => { if (!closed) setPlayBlocked(true); });
      }
    };
    peer.onconnectionstatechange = () => {
      if (!closed) setConnection(peer.connectionState === 'connected' ? 'Video en vivo conectado'
        : peer.connectionState === 'failed' ? 'No se pudo conectar el video. Usa el mismo Wi-Fi y pulsa Reconectar.' : 'Conectando…');
    };
    const poll = async () => {
      try {
        const result = await api<State>(`/live-sessions/${id}/monitor/`);
        if (closed) return;
        setState(result);
        if (result.status !== 'processing') {
          setConnection('La sesión terminó.'); peer.close(); return;
        }
        if (result.answer?.viewer === viewer && !answered) {
          await peer.setRemoteDescription({ type: 'answer', sdp: result.answer.sdp });
          answered = true;
        }
        if (result.offer && result.offer.viewer !== viewer) {
          setConnection('Otro monitor tomó la conexión. Pulsa Reconectar para recuperarla.'); peer.close(); return;
        }
      } catch (e) { if (!closed) { setError(errorText(e)); peer.close(); return; } }
      if (!closed) timer = setTimeout(() => void poll(), 1500);
    };
    const start = async () => {
      try {
        peer.addTransceiver('video', { direction: 'recvonly' });
        await peer.setLocalDescription(await peer.createOffer());
        await gatherIce(peer);
        if (closed) return;
        await api(`/live-sessions/${id}/monitor/`, 'POST', { kind: 'offer', viewer, sdp: peer.localDescription!.sdp });
        if (!closed) void poll();
      } catch (e) { if (!closed) setError(errorText(e)); }
    };
    void start();
    return () => {
      closed = true; clearTimeout(timer); peer.close();
      if (video.current) video.current.srcObject = null;
    };
  }, [id, attempt]);
  return <><PageHeader title="Monitor de cámara" subtitle="Video del teléfono y conteos de la última muestra analizada." />
    <div className="page-body"><Message text={error} />
      <section className="panel settings-panel">
        <h2>{connection}</h2>
        <p>Mantén el teléfono abierto en su sesión de cámara. Ambos equipos deben usar la misma cuenta y una red Wi-Fi que permita conectarlos.</p>
        <video ref={video} autoPlay muted playsInline style={{ width: '100%', maxWidth: 960 }} />
        {playBlocked && <button className="button primary" onClick={() => void video.current?.play().then(() => setPlayBlocked(false)).catch(() => setError('Pulsa Reconectar para intentar reproducir el video.'))}>Reproducir video</button>}
        <p role="status">{state?.latest ? `Personas: ${state.latest.people} · Máximo de sesión: ${state.latest.people_max} · Muestras: ${state.latest.samples}` : 'Sin muestras recientes. Comprueba el teléfono.'}</p>
        {state?.latest && <p>Última detección: {new Date(state.latest.received_at).toLocaleTimeString()} · Ocupación: {state.capacity ? `${(state.latest.people / state.capacity * 100).toFixed(1)}%` : 'sin capacidad validada'}</p>}
        <p className="small-muted">El video es continuo. Los conteos se actualizan por muestras y pueden llevar retraso. No se graba video en el servidor. Esta vista no inicia ni detiene la sesión del teléfono.</p>
        <button className="button secondary" onClick={() => setAttempt(n => n + 1)}>Reconectar</button>
        <Link className="button secondary" to="/analisis/en-vivo">Volver a cámara</Link>
      </section>
    </div></>;
}
