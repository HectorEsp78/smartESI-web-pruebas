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
    throw new Error(`No se pudieron cargar los datos (${response.status}).`);
  }

  return (await response.json()) as T;
}

export function buildQuery(params: Record<string, string>): string {
  return new URLSearchParams(params).toString();
}
