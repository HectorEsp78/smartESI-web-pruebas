import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, getJson } from './http';

function stubResponse(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: false, status, json: async () => body }),
  );
}

describe('getJson', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('prefers the message sent by the server, also on a 404', async () => {
    stubResponse(404, { detail: 'Estancia no encontrada.' });

    const error = await getJson('/x').catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(404);
    expect((error as ApiError).message).toBe('Estancia no encontrada.');
  });

  it('falls back to a generic message when the body has no detail', async () => {
    stubResponse(502, { other: true });

    await expect(getJson('/x')).rejects.toThrow('No se pudieron cargar los datos (502).');
  });

  it('explains network failures in Spanish', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));

    await expect(getJson('/x')).rejects.toThrow('No se pudo conectar con el servidor.');
  });

  it('does not disguise a cancelled request', async () => {
    const controller = new AbortController();
    controller.abort();
    const abortError = new DOMException('Aborted', 'AbortError');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(abortError));

    await expect(getJson('/x', controller.signal)).rejects.toBe(abortError);
  });
});
