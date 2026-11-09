import { resolveApiPath } from './baseUrl';

/** The server answered with an error status. */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** Message sent by FastAPI as `{detail: "..."}`, when the body has one. */
async function readDetail(response: Response): Promise<string | null> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    return typeof body.detail === 'string' && body.detail.trim() ? body.detail : null;
  } catch {
    return null;
  }
}

function fallbackMessage(status: number): string {
  return status === 404
    ? 'No se encontró el recurso solicitado.'
    : `No se pudieron cargar los datos (${status}).`;
}

export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(resolveApiPath(path), {
      method: 'GET',
      signal,
      headers: { Accept: 'application/json' },
    });
  } catch (error) {
    // React Query cancels requests on purpose: that is not a failure to report.
    if (signal?.aborted) throw error;
    throw new Error('No se pudo conectar con el servidor.', { cause: error });
  }

  if (!response.ok) {
    const detail = await readDetail(response);
    throw new ApiError(detail ?? fallbackMessage(response.status), response.status);
  }

  return (await response.json()) as T;
}

export function buildQuery(params: Record<string, string>): string {
  return new URLSearchParams(params).toString();
}
