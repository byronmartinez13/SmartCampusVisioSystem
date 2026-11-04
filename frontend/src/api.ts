export type User = {
  id: number; name: string; email: string; role: 'admin' | 'coordinator' | 'viewer'; role_label: string; is_active: boolean;
};
export type DashboardData = {
  classrooms: number; analyzed_classrooms: number; open_alerts: number; week_start: string;
  occupancy: { date: string; percent: number | null }[];
};

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export async function downloadPdf(path: string, filename: string): Promise<void> {
  const response = await fetch(`/api${path}`, { credentials: 'same-origin', cache: 'no-store' });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(data ? formatError(data) : 'No se pudo descargar el reporte.', response.status);
  }
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement('a');
  anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function formatError(value: unknown): string {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(formatError).join(' ');
  if (value && typeof value === 'object') return Object.values(value).map(formatError).join(' ');
  return 'No se pudo completar la solicitud.';
}

export async function api<T>(path: string, method = 'GET', data?: unknown): Promise<T> {
  const headers: Record<string, string> = data instanceof FormData ? {} : { 'Content-Type': 'application/json' };
  if (method !== 'GET') {
    const csrf = await fetch('/api/auth/csrf/', { credentials: 'same-origin', cache: 'no-store' });
    if (!csrf.ok) throw new ApiError('No se pudo establecer una conexión segura. Inténtalo de nuevo.', csrf.status);
    headers['X-CSRFToken'] = (await csrf.json()).csrfToken;
  }
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      method, headers, credentials: 'same-origin', cache: 'no-store',
      body: data instanceof FormData ? data : data === undefined ? undefined : JSON.stringify(data),
    });
  } catch {
    throw new ApiError('No hay conexión con el servidor. Comprueba que esté disponible.', 0);
  }
  if (response.status === 204) return undefined as T;
  const json = await response.json().catch(() => ({ detail: 'El servidor no está disponible. Inténtalo de nuevo.' }));
  if (!response.ok) {
    if (response.status === 403 && path !== '/auth/me/' && !path.startsWith('/auth/login')) {
      window.dispatchEvent(new Event('session-check'));
    }
    throw new ApiError(formatError(json), response.status);
  }
  return json as T;
}
