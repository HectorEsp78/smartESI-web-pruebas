import { resolveApiPath } from './baseUrl';

export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(resolveApiPath(path), {
    method: 'GET',
    signal,
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('No se encontró el recurso solicitado.');
    }
    // FastAPI returns validation/business errors as ``{detail: "..."}``. Show
    // that message when possible (for example, when two periods have a
    // different number of buckets).
    let detail: string | null = null;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === 'string' && body.detail.trim()) {
        detail = body.detail;
      }
    } catch {
      // Keep the generic message when the body is not JSON.
    }
    if (detail) throw new Error(detail);
    throw new Error(`No se pudieron cargar los datos (${response.status}).`);
  }

  return (await response.json()) as T;
}

export function buildQuery(params: Record<string, string>): string {
  return new URLSearchParams(params).toString();
}
