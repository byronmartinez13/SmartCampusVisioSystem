import { useState } from 'react';
import { api } from './api';
import { errorText } from './campus/shared';

export function DeleteAnalysisButton({ id, name, onDeleted, onError }: {
  id: string; name: string; onDeleted: () => void; onError: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  async function remove() {
    if (!window.confirm(`¿Eliminar definitivamente «${name}»?\n\nSe eliminarán el análisis, su video y vista previa, el resumen guardado y las alertas asociadas. Desaparecerá de reportes y dashboard. No se puede deshacer. Los PDF o videos ya descargados en otros equipos no se borran.`)) return;
    setBusy(true); onError('');
    try { await api(`/video-analyses/${id}/`, 'DELETE'); onDeleted(); }
    catch (e) { onError(errorText(e)); }
    finally { setBusy(false); }
  }
  return <button className="button secondary small" disabled={busy} onClick={() => void remove()}>{busy ? 'Eliminando…' : 'Eliminar análisis'}</button>;
}
